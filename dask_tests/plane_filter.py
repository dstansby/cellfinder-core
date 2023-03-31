from cellfinder_core.tools.IO import read_with_dask

signal_data_path = (
    "/Users/dstansby/brainglobe-data/test_brain_SK_AA_71_3_subset/ch01_subset"
)

signal_array = read_with_dask(signal_data_path)

signal_array.visualize(filename="signal_array.png")
