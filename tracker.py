import cv2
import numpy as np

class BehaviorEngine:
    def __init__(self, loiter_thresh, move_thresh, zone_polygon):
        self.loiter_thresh = loiter_thresh
        self.move_thresh = move_thresh
        self.zone_polygon = zone_polygon
        
        # Track historical positions and timestamps for each person ID
        self.first_seen = {}
        self.stationary_start = {}
        self.last_pos = {}
        self.last_logged_time = {}

    def analyze(self, track_id, foot_point, current_time):
        cx, cy = foot_point

        # If ID is seen for the first time, register baseline coordinates
        if track_id not in self.first_seen:
            self.first_seen[track_id] = current_time
            self.stationary_start[track_id] = current_time
            self.last_pos[track_id] = (cx, cy)
            self.last_logged_time[track_id] = 0

        # Calculate movement distance (Euclidean distance)
        px, py = self.last_pos[track_id]
        distance = np.hypot(cx - px, cy - py)

        # If person moved more than noise threshold, reset their stationary timer
        if distance > self.move_thresh:
            self.stationary_start[track_id] = current_time
            self.last_pos[track_id] = (cx, cy)

        stationary_duration = current_time - self.stationary_start[track_id]

        # Check if foot coordinates are inside the restricted boundary polygon
        inside_zone = cv2.pointPolygonTest(self.zone_polygon, (float(cx), float(cy)), False) >= 0

        # Decide behavior state
        if inside_zone:
            return "ZONE BREACH", (0, 0, 255), True  # Red
        elif stationary_duration >= self.loiter_thresh:
            return f"Loitering ({int(stationary_duration)}s)", (0, 165, 255), True  # Orange
        else:
            return "Moving (Normal)", (0, 255, 0), False  # Green