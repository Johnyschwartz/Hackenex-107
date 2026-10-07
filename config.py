import numpy as np

# Camera Source: 0 uses your laptop webcam
VIDEO_SOURCE = 0

# Model parameters
MODEL_NAME = "yolov8n.pt"

# Behavioral Thresholds
LOITERING_TIME_SEC = 5.0      # Flag as loitering if stationary > 5 seconds
PIXEL_MOVEMENT_THRESH = 35    # Movement noise tolerance (in pixels)

# Restricted Area Boundary [X, Y] (Top-left corner of the camera frame)
RESTRICTED_ZONE = np.array([
    [30, 30],
    [300, 30],
    [300, 320],
    [30, 320]
], np.int32)

LOG_FILE = "incidents.csv"