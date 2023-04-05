import webbrowser

from dask.distributed import Client

from cellfinder_core.main import main
from cellfinder_core.tools.IO import read_with_dask

if __name__ == "__main__":
    client = Client()
    webbrowser.open_new_tab(client.dashboard_link)

    signal_data_path = (
        "/Users/dstansby/brainglobe-data/"
        "test_brain_SK_AA_71_3_subset/ch01_subsubset"
    )

    signal_array = read_with_dask(signal_data_path)
    plane_size_mb = (
        signal_array.itemsize
        * signal_array.shape[1]
        * signal_array.shape[2]
        / 1000
        / 1000
    )

    print(f"Plane size: {plane_size_mb:.02f} MB")

    structs = main(
        signal_array,
        background_array=signal_array,
        voxel_sizes=[5, 2, 2],
        ball_z_size=15,
        ball_xy_size=4,
    )
    print(structs)
