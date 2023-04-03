import dask.array as da
from dask import delayed
from dask.distributed import Client
import numpy as np

from cellfinder_core.detect.filters.plane.plane_filter import get_tile_mask
from cellfinder_core.detect.filters.setup_filters import setup_tile_filtering
from cellfinder_core.tools.IO import read_with_dask

if __name__ == "__main__":
    client = Client(threads_per_worker=1, n_workers=4)
    print(client.dashboard_link)

    signal_data_path = "/Users/dstansby/brainglobe-data/test_brain_SK_AA_71_3_subset/ch01_subset"

    signal_array = read_with_dask(signal_data_path)

    clipping_value, threshold_value = setup_tile_filtering(signal_array[0])
    ball_z_size = 3

    @delayed
    def _get_tile_mask(plane):
        return get_tile_mask(plane, clipping_value, threshold_value, 4, 0.2, 10)

    @delayed
    def _ball_filter(plane_masks: list):
        pass

    tile_masks = []
    for plane in signal_array[:20]:
        tile_masks.append(_get_tile_mask(plane))

    ball_filtered_planes = []
    for i in range(0, len(tile_masks) - ball_z_size):
        ball_filtered_planes.append(_ball_filter(tile_masks[i:i+ball_z_size]))

    ball_filtered_planes = delayed(ball_filtered_planes)
    ball_filtered_planes.visualize(filename="ball_filtered.png")
