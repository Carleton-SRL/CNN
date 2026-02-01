import dv_processing as dv
import numpy as np
import h5py
import os
import argparse

# Sample terminal run command
'''
python3 importAEDAT4toHDF5.py --input '/home/alexandercrain/Dropbox/Graduate Documents/Doctor of Philosophy/Thesis Research/Datasets/SPOT/Jack Woolridge/recording_20260127_145247.aedat4' --output '/home/alexandercrain/Dropbox/Graduate Documents/Doctor of Philosophy/Thesis Research/Datasets/SPOT/HDF5/recording_20260127_145247.hdf5'
'''

# Setup argparser
parser = argparse.ArgumentParser(description="Convert AEDAT4 event data to HDF5.")
parser.add_argument("-i", "--input", required=True, help="Path to input .aedat4 file")
parser.add_argument("-o", "--output", required=True, help="Path to output .h5 file")

# Parse the arguments from the command line
args = parser.parse_args()

# Assign the arguments to your variables
input_file = args.input
output_file = args.output

print(f"Processing input: {input_file}")
print(f"Saving output to: {output_file}")

# Import the data
reader = dv.io.MonoCameraRecording(input_file)

# Chunk size for HDF5 writing (affects compression/access speed)
CHUNK_SIZE = 100000 

print(f"Processing {input_file}...")

with h5py.File(output_file, "w") as f:
    # Create resizable datasets. 
    # Timestamps need int64. Coordinates fit in uint16. Polarity fits in uint8.
    dset_t = f.create_dataset("timestamp", (0,), maxshape=(None,), dtype="int64", chunks=(CHUNK_SIZE,))
    dset_x = f.create_dataset("x", (0,), maxshape=(None,), dtype="uint16", chunks=(CHUNK_SIZE,))
    dset_y = f.create_dataset("y", (0,), maxshape=(None,), dtype="uint16", chunks=(CHUNK_SIZE,))
    dset_p = f.create_dataset("polarity", (0,), maxshape=(None,), dtype="uint8", chunks=(CHUNK_SIZE,))

    total_events = 0

    while reader.isRunning():
        # Get next batch of events
        batch = reader.getNextEventBatch()
        
        if batch is not None and batch.size() > 0:
            # Convert directly to numpy structured array
            numpy_batch = batch.numpy()

            # Extract columns
            t_chunk = numpy_batch['timestamp']
            x_chunk = numpy_batch['x']
            y_chunk = numpy_batch['y']
            p_chunk = numpy_batch['polarity']
                
            # Get the length
            n_new = len(t_chunk)
            
            # Resize datasets to accommodate new data
            dset_t.resize(dset_t.shape[0] + n_new, axis=0)
            dset_x.resize(dset_x.shape[0] + n_new, axis=0)
            dset_y.resize(dset_y.shape[0] + n_new, axis=0)
            dset_p.resize(dset_p.shape[0] + n_new, axis=0)
            
            # Append new data
            dset_t[-n_new:] = t_chunk
            dset_x[-n_new:] = x_chunk
            dset_y[-n_new:] = y_chunk
            dset_p[-n_new:] = p_chunk

            total_events += n_new
            print(f"\rProcessed {total_events} events...", end="")

print(f"\nDone! Saved {total_events} events to {output_file}")
