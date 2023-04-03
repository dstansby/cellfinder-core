from typing import Tuple

import dask.array as da
import numpy as np

from cellfinder_core.detect.filters.plane.classical_filter import enhance_peaks
from cellfinder_core.detect.filters.plane.tile_walker import TileWalker


def get_tile_mask(
    plane: da.array,
    clipping_value: float,
    threshold_value: float,
    soma_diameter: float,
    log_sigma_size: float,
    n_sds_above_mean_thresh: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    This thresholds the input plane, and returns a mask indicating which
    tiles are inside the brain.

    The input plane is:

    1. Clipped to self.threshold value
    2. Run through a peak enhancement filter (see `classical_filter.py`)
    3. Thresholded. Any values that are larger than
        (mean + stddev * self.n_sds_above_mean_thresh) are set to
        self.threshold_value in-place.

    Parameters
    ----------
    plane :
        Input plane.

    Returns
    -------
    plane :
        Thresholded plane.
    inside_brain_tiles :
        Boolean mask indicating which tiles are inside (1) or
        outside (0) the brain.
    """
    laplace_gaussian_sigma = log_sigma_size * soma_diameter
    plane = plane.T
    plane = np.clip(plane, 0, clipping_value)
    # Read plane from a dask array into memory as a numpy array
    plane = np.array(plane)

    # Get tiles that are within the brain
    walker = TileWalker(plane, soma_diameter)
    walker.mark_bright_tiles()
    inside_brain_tiles = walker.bright_tiles_mask.astype(np.uint8)

    # Threshold the image
    thresholded_img = enhance_peaks(
        plane.copy(),
        clipping_value,
        gaussian_sigma=laplace_gaussian_sigma,
    )
    avg = np.mean(thresholded_img)
    sd = np.std(thresholded_img)
    threshold = avg + n_sds_above_mean_thresh * sd
    plane[thresholded_img > threshold] = threshold_value

    return plane, inside_brain_tiles
