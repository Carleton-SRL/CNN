import h5py
import numpy as np
import os
import pyvista as pv

# Import data from HDF5 file
with h5py.File('recording_20251029_131131.h5', 'r') as f:
    tk = f['/timestamp'][:].astype(np.float64)
    xk = f['/x'][:].astype(np.float64)
    yk = f['/y'][:].astype(np.float64)
    pk = f['/polarity'][:].astype(np.float64)

# Convert time to seconds from start
tk = (tk - tk[0]) / 1e6  # [seconds]

# Define start and end time to process [seconds]
t_start_process = 60.0
t_end_process = 70.0

# Find indices within the valid range (boolean indexing)
valid_idx = (tk >= t_start_process) & (tk <= t_end_process)

# Filter the data vectors
tk = tk[valid_idx]
xk = xk[valid_idx]
yk = yk[valid_idx]
pk = pk[valid_idx]

# Shift time to start at 0 for the new window
tk = tk - t_start_process

# Create point cloud
points = np.column_stack([xk/640, yk/480, tk/tk.max()])
point_cloud = pv.PolyData(points)
point_cloud['timestamp'] = tk/tk.max()

# Plot
plotter = pv.Plotter()
plotter.add_points(point_cloud, scalars='timestamp',
                   cmap='viridis', point_size=1)
plotter.show()
