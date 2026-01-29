import dv_processing as dv
import numpy as np
from scipy.io import savemat

# Import the AEDAT4 data
reader = dv.io.MonoCameraRecording("recording_20251029_131131.aedat4")

# Loop through the data and append
events = []
while reader.isRunning():
    batch = reader.getNextEventBatch()
    if batch:
        for e in batch:
            events.append([e.timestamp(), e.x(), e.y(), e.polarity()])

# Convert to NumPy array (float64 by default)
events = np.array(events, dtype=np.float64)

# Save as MATLAB .mat file
savemat("recording_20251029_131131.mat", {"events": events})
