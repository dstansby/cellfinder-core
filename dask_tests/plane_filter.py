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

    @delayed
    def processed_mean(plane):
        plane, _ = get_tile_mask(plane, clipping_value, threshold_value, 4, 0.2, 10)
        return np.mean(plane)

    new_planes = []
    for plane in signal_array[:20]:
        new_planes.append(processed_mean(plane))

    new_planes = delayed(new_planes)
    new_planes.visualize(filename="plane_filtered.png")
    new_planes = new_planes.compute()
    print(new_planes)
