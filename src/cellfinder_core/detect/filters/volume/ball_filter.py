from typing import Optional

import numpy as np
from numba import jit

from cellfinder_core.tools.array_operations import bin_mean_3d
from cellfinder_core.tools.geometry import make_sphere

DEBUG = False


class BallFilter:
    def __init__(
        self,
        layer_width,
        layer_height,
        ball_xy_size,
        ball_z_size: int,
        overlap_fraction=0.8,
        tile_step_width=None,
        tile_step_height=None,
        threshold_value: Optional[int] = None,
        soma_centre_value=None,
    ):
        self.ball_xy_size = ball_xy_size
        self.ball_z_size = ball_z_size
        self.overlap_fraction = overlap_fraction
        self.tile_step_width = tile_step_width
        self.tile_step_height = tile_step_height

        self.THRESHOLD_VALUE = threshold_value
        self.SOMA_CENTRE_VALUE = soma_centre_value

        # Create a spherical kernel.
        #
        # This is done by:
        # 1. Generating a binary sphere at a resolution *upscale_factor* larger
        #    than desired.
        # 2. Downscaling the binary sphere to get a 'fuzzy' sphere at the
        #    original intended scale
        upscale_factor: int = 7
        upscaled_kernel_shape = (
            upscale_factor * ball_xy_size,
            upscale_factor * ball_xy_size,
            upscale_factor * ball_z_size,
        )
        upscaled_ball_centre_position = (
            np.floor(upscaled_kernel_shape[0] / 2),
            np.floor(upscaled_kernel_shape[1] / 2),
            np.floor(upscaled_kernel_shape[2] / 2),
        )
        upscaled_ball_radius = upscaled_kernel_shape[0] / 2.0
        sphere_kernel = make_sphere(
            upscaled_kernel_shape,
            upscaled_ball_radius,
            upscaled_ball_centre_position,
        )
        sphere_kernel = sphere_kernel.astype(np.float64)
        self.kernel = bin_mean_3d(
            sphere_kernel,
            bin_height=upscale_factor,
            bin_width=upscale_factor,
            bin_depth=upscale_factor,
        )

        assert (
            self.kernel.shape[2] == ball_z_size
        ), "Kernel z dimension should be {}, got {}".format(
            ball_z_size, self.kernel.shape[2]
        )

        self.overlap_threshold = np.sum(self.overlap_fraction * self.kernel)

        # Stores the current planes that are being filtered
        self.volume = np.empty(
            (layer_width, layer_height, ball_z_size), dtype=np.uint16
        )
        # Index of the middle plane in the volume
        self.middle_z_idx = int(np.floor(ball_z_size / 2))

        # TODO: lazy initialisation
        self.good_tiles_mask = np.empty(
            (
                int(np.ceil(layer_width / tile_step_width)),
                int(np.ceil(layer_height / tile_step_height)),
                ball_z_size,
            ),
            dtype=np.uint8,
        )
        # Stores the z-index in volume at which new layers are inserted when
        # append() is called
        self.__current_z = -1

    @property
    def ready(self):
        """
        Return `True` if enough layers have been appended to run the filter.
        """
        return self.__current_z == self.ball_z_size - 1

    def append(self, layer, mask):
        """
        Add a new 2D layer to the filter.
        """
        if DEBUG:
            assert [e for e in layer.shape[:2]] == [
                e for e in self.volume.shape[:2]
            ], 'layer shape mismatch, expected "{}", got "{}"'.format(
                [e for e in self.volume.shape[:2]],
                [e for e in layer.shape[:2]],
            )
            assert [e for e in mask.shape[:2]] == [
                e for e in self.good_tiles_mask.shape[2]
            ], 'mask shape mismatch, expected"{}", got {}"'.format(
                [e for e in self.good_tiles_mask.shape[:2]],
                [e for e in mask.shape[:2]],
            )
        if not self.ready:
            self.__current_z += 1
        else:
            # Shift everything down by one to make way for the new layer
            self.volume = np.roll(
                self.volume, -1, axis=2
            )  # WARNING: not in place
            self.good_tiles_mask = np.roll(self.good_tiles_mask, -1, axis=2)
        # Add the new layer to the top of volume and good_tiles_mask
        self.volume[:, :, self.__current_z] = layer[:, :]
        self.good_tiles_mask[:, :, self.__current_z] = mask[:, :]

    def get_middle_plane(self):
        """
        Get the plane in the middle of self.volume.
        """
        z = self.middle_z_idx
        return np.array(self.volume[:, :, z], dtype=np.uint16)

    def walk(self):  # Highly optimised because most time critical
        ball_radius = self.ball_xy_size // 2
        # Get extents of image that are covered by tiles
        tile_mask_covered_img_width = (
            self.good_tiles_mask.shape[0] * self.tile_step_width
        )
        tile_mask_covered_img_height = (
            self.good_tiles_mask.shape[1] * self.tile_step_height
        )
        # Get maximum offsets for the ball
        max_width = tile_mask_covered_img_width - self.ball_xy_size
        max_height = tile_mask_covered_img_height - self.ball_xy_size

        _walk(
            max_height,
            max_width,
            self.tile_step_width,
            self.tile_step_height,
            self.good_tiles_mask,
            self.volume,
            self.kernel,
            ball_radius,
            self.middle_z_idx,
            self.overlap_threshold,
            self.THRESHOLD_VALUE,
            self.SOMA_CENTRE_VALUE,
        )


@jit(nopython=True, cache=True)
def _cube_overlaps(
    cube: np.ndarray,
    overlap_threshold: float,
    THRESHOLD_VALUE: int,
    kernel: np.ndarray,
) -> bool:  # Highly optimised because most time critical
    """
    For each pixel in cube that is greater than THRESHOLD_VALUE, sum
    up the corresponding pixels in *kernel*. If the total is less than
    overlap_threshold, return False, otherwise return True.

    Halfway through scanning the z-planes, if the total overlap is
    less than 0.4 * overlap_threshold, this will return False early
    without scanning the second half of the z-planes.

    Parameters
    ----------
    cube :
        3D array.
    overlap_threshold :
        Threshold above which to return True.
    THRESHOLD_VALUE :
        Value above which a pixel is marked as being part of a cell.
    kernel :
        3D array, with the same shape as *cube*.
    """
    current_overlap_value = 0

    middle = np.floor(cube.shape[2] / 2) + 1
    halfway_overlap_thresh = (
        overlap_threshold * 0.4
    )  # FIXME: do not hard code value

    for z in range(cube.shape[2]):
        # TODO: OPTIMISE: step from middle to outer boundaries to check
        # more data first
        #
        # If halfway through the array, and the overlap value isn't more than
        # 0.4 * the overlap threshold, return
        if z == middle and current_overlap_value < halfway_overlap_thresh:
            return False  # DEBUG: optimisation attempt
        for y in range(cube.shape[1]):
            for x in range(cube.shape[0]):
                # includes self.SOMA_CENTRE_VALUE
                if cube[x, y, z] >= THRESHOLD_VALUE:
                    current_overlap_value += kernel[x, y, z]
    return current_overlap_value > overlap_threshold


@jit(nopython=True)
def _is_tile_to_check(
    x: int,
    y: int,
    middle_z: int,
    tile_step_width: int,
    tile_step_height: int,
    good_tiles_mask: np.ndarray,
):  # Highly optimised because most time critical
    """
    Check if the tile containing pixel (x, y) is a tile that needs checking.
    """
    x_in_mask = x // tile_step_width  # TEST: test bounds (-1 range)
    y_in_mask = y // tile_step_height  # TEST: test bounds (-1 range)
    return good_tiles_mask[x_in_mask, y_in_mask, middle_z]


@jit(nopython=True)
def _walk(
    max_height: int,
    max_width: int,
    tile_step_width: int,
    tile_step_height: int,
    good_tiles_mask: np.ndarray,
    volume: np.ndarray,
    kernel: np.ndarray,
    ball_radius: int,
    middle_z: int,
    overlap_threshold: float,
    THRESHOLD_VALUE: int,
    SOMA_CENTRE_VALUE: int,
) -> None:
    """
    Scan through *volume*, and mark pixels where there are enough surrounding
    pixels with high enough intensity.

    The surrounding area is defined by the *kernel*.

    Parameters
    ----------
    max_height, max_width :
        Maximum offsets for the ball filter.
    good_tiles_mask :
        Array containing information on whether a tile needs checking
        or not.
    volume :
        3D array containing the plane-filtered data.
    kernel :
        3D array
    ball_radius :
        Radius of the ball in the xy plane.
    SOMA_CENTRE_VALUE :
        Value that is used to mark pixels in *volume*.

    Notes
    -----
    Warning: modifies volume in place!
    """
    for y in range(max_height):
        for x in range(max_width):
            ball_centre_x = x + ball_radius
            ball_centre_y = y + ball_radius
            if _is_tile_to_check(
                ball_centre_x,
                ball_centre_y,
                middle_z,
                tile_step_width,
                tile_step_height,
                good_tiles_mask,
            ):
                cube = volume[
                    x : x + kernel.shape[0],
                    y : y + kernel.shape[1],
                    :,
                ]
                if _cube_overlaps(
                    cube,
                    overlap_threshold,
                    THRESHOLD_VALUE,
                    kernel,
                ):
                    volume[
                        ball_centre_x, ball_centre_y, middle_z
                    ] = SOMA_CENTRE_VALUE
