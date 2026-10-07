import os
import csv
import cv2
import time
import winsound
import threading
import smtplib
from datetime import datetime
from email.message import EmailMessage
import numpy as np
import pyttsx3
from ultralytics import YOLO
import config
from tracker import BehaviorEngine

# ==========================================
# 1. EMAIL CONFIGURATION
# ==========================================
SENDER_EMAIL = "yyy"
SENDER_APP_PASSWORD = "xxx"
RECIPIENT_EMAIL = "yyy"

def send_alert_email_async(image_path, entity_id, date_str, time_str, action_desc, breach_status):
    """Sends detailed email report with formatted timestamp and intruder photo in background."""
    def _worker():
        try:
            msg = EmailMessage()
            msg['Subject'] = f"🚨 [SECURITY INCIDENT] Unauthorized Entity Detected (ID #{entity_id})"
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECIPIENT_EMAIL

            body = f"""
AUTONOMOUS SURVEILLANCE AUDIT DISPATCH
==================================================
Date & Time       : {date_str} at {time_str}
Detected Entity   : ID #{entity_id}
Authorization     : UNAUTHORIZED INTRUDER
Current Activity  : {action_desc}
Perimeter Status  : {breach_status}
Location Assigned : Restricted Server Room Vault
==================================================
Forensic evidence crop is attached to this transmission.
"""
            msg.set_content(body)

            if os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(image_path)
                msg.add_attachment(file_data, maintype='image', subtype='jpeg', filename=file_name)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
                server.send_message(msg)

            print(f"[EMAIL SENT] Incident report dispatched to {RECIPIENT_EMAIL} for ID #{entity_id}")

        except Exception as e:
            print(f"[!] Email dispatch failed: {e}")

    threading.Thread(target=_worker, daemon=True).start()


# ==========================================
# 2. ALARM SIREN & AUDIO ENGINE
# ==========================================
AUTH_DIR = os.path.join("evidence", "authorized")
UNAUTH_DIR = os.path.join("evidence", "unauthorized")
os.makedirs(AUTH_DIR, exist_ok=True)
os.makedirs(UNAUTH_DIR, exist_ok=True)

with open(config.LOG_FILE, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "Time", "Entity_ID", "Auth_Status", "Action_State", "Perimeter_Status", "Snapshot_File"])

last_alarm_time = 0
ALARM_COOLDOWN_SEC = 4.0

def trigger_siren_and_voice_async(voice_message):
    def _worker():
        try:
            for _ in range(2):
                winsound.Beep(1200, 140)
                winsound.Beep(800, 140)

            engine_voice = pyttsx3.init()
            engine_voice.setProperty('rate', 165)
            engine_voice.say(voice_message)
            engine_voice.runAndWait()
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()


# ==========================================
# 3. ROBUST MULTI-FEATURE BIOMETRIC ENGINE
# ==========================================
enrolled_face_hist = None

def get_face_descriptor(crop_img):
    """Extracts a combined HSV + Intensity descriptor resilient to slight angle & lighting changes."""
    if crop_img is None or crop_img.size == 0:
        return None
    resized = cv2.resize(crop_img, (96, 96))
    
    # 1. Color HSV histogram
    hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    hist_hsv = cv2.calcHist([hsv], [0, 1], None, [24, 24], [0, 180, 0, 256])
    cv2.normalize(hist_hsv, hist_hsv, 0, 1, cv2.NORM_MINMAX)
    
    # 2. Grayscale intensity structural histogram
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    hist_gray = cv2.calcHist([gray], [0], None, [32], [0, 256])
    cv2.normalize(hist_gray, hist_gray, 0, 1, cv2.NORM_MINMAX)
    
    return hist_hsv, hist_gray

def compare_descriptors(desc1, desc2):
    if desc1 is None or desc2 is None:
        return 0.0
    hsv_sim = cv2.compareHist(desc1[0], desc2[0], cv2.HISTCMP_CORREL)
    gray_sim = cv2.compareHist(desc1[1], desc2[1], cv2.HISTCMP_CORREL)
    # Balanced score
    return 0.65 * max(0, hsv_sim) + 0.35 * max(0, gray_sim)

def extract_head_region(frame, box):
    x1, y1, x2, y2 = box
    h = max(1, y2 - y1)
    head_y2 = y1 + int(h * 0.38)
    return frame[max(0, y1):min(frame.shape[0], head_y2), max(0, x1):min(frame.shape[1], x2)]

def classify_action(box, behavior_string):
    x1, y1, x2, y2 = box
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)
    aspect_ratio = w / float(h)

    if "Moving" in behavior_string:
        return "Moving / Walking"
    else:
        if aspect_ratio >= 0.70:
            return f"Sitting / Crouching ({behavior_string})"
        else:
            return f"Standing Still ({behavior_string})"


# ==========================================
# 4. RUNTIME VIDEO INGESTION & PIPELINE
# ==========================================
model = YOLO(config.MODEL_NAME)
engine = BehaviorEngine(config.LOITERING_TIME_SEC, config.PIXEL_MOVEMENT_THRESH, config.RESTRICTED_ZONE)
cap = cv2.VideoCapture(config.VIDEO_SOURCE)
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

# Tracking & Biometric States
id_authorization = {}       # id -> True / False
id_match_scores = {}        # id -> list of recent correlation scores
snapped_entities = set()    # track_ids already snapped and emailed
frame_idx = 0

print("\n" + "="*60)
print("  MULTI-PERSON SECURE ACCESS CONTROL SYSTEM")
print("  Press 's' -> Register Authorized Admin (Locks in memory)")
print("  Press 'q' -> Exit Demo")
print("="*60 + "\n")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_idx += 1
    current_time_sec = frame_idx / fps
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    # Draw Restricted Server Vault Perimeter
    cv2.polylines(frame, [config.RESTRICTED_ZONE], isClosed=True, color=(0, 0, 255), thickness=2)
    cv2.putText(frame, "RESTRICTED SERVER ROOM", 
                (config.RESTRICTED_ZONE[0][0], max(config.RESTRICTED_ZONE[0][1] - 8, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

    results = model.track(frame, persist=True, classes=[0], conf=0.40, tracker="bytetrack.yaml", verbose=False)
    threat_active = False

    current_boxes = []
    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        ids = results[0].boxes.id.cpu().numpy().astype(int)
        current_boxes = list(zip(boxes, ids))

        for box, track_id in current_boxes:
            x1, y1, x2, y2 = box
            foot_coord = (int((x1 + x2) / 2), y2)
            head_crop = extract_head_region(frame, box)
            full_crop = frame[max(0, y1):min(frame.shape[0], y2), max(0, x1):min(frame.shape[1], x2)]

            # -------------------------------------------------------------
            # STICKY MULTI-PERSON BIOMETRIC EVALUATION
            # -------------------------------------------------------------
            if enrolled_face_hist is not None:
                # If this ID is already confirmed authorized, keep it authorized!
                if id_authorization.get(track_id) is True:
                    pass  # Retain admin status without flickering
                else:
                    # Check every 4 frames or when first seen
                    if track_id not in id_match_scores or frame_idx % 4 == 0:
                        if head_crop.size > 0:
                            curr_desc = get_face_descriptor(head_crop)
                            score = compare_descriptors(enrolled_face_hist, curr_desc)
                            
                            if track_id not in id_match_scores:
                                id_match_scores[track_id] = []
                            id_match_scores[track_id].append(score)
                            if len(id_match_scores[track_id]) > 5:
                                id_match_scores[track_id].pop(0)

                            # If average correlation passes 0.48, authorize this ID permanently
                            avg_score = sum(id_match_scores[track_id]) / len(id_match_scores[track_id])
                            if avg_score >= 0.48:
                                id_authorization[track_id] = True
                            else:
                                id_authorization[track_id] = False
            else:
                id_authorization[track_id] = None

            is_auth = id_authorization.get(track_id)
            behavior, _, is_spatial_anomaly = engine.analyze(track_id, foot_coord, current_time_sec)
            action_desc = classify_action(box, behavior)

            if enrolled_face_hist is None:
                status_color = (0, 165, 255)
                display_label = f"ID #{track_id}: PRESS 's' TO ENROLL"
            elif is_auth is True:
                # Confirmed Admin (Always Green, No False Drops)
                status_color = (0, 255, 0)
                display_label = f"ID #{track_id} [ADMIN]: {action_desc}"
            else:
                # Unauthorized Intruder (Red)
                status_color = (0, 0, 255)
                threat_active = True
                
                is_breach = "ZONE BREACH" in behavior
                breach_status = "CRITICAL VAULT INTRUSION" if is_breach else "PERIMETER PROXIMITY"
                display_label = f"ID #{track_id} [UNAUTHORIZED]: {action_desc}"

                # Trigger Dual Siren + Voice Alert
                if current_time_sec - last_alarm_time >= ALARM_COOLDOWN_SEC:
                    last_alarm_time = current_time_sec
                    voice_msg = "Warning! Restricted server room breach!" if is_breach else "Warning! Unauthorized person detected!"
                    trigger_siren_and_voice_async(voice_msg)

                # Capture separate snapshot & email for EVERY individual intruder
                if track_id not in snapped_entities and full_crop.size > 0:
                    snapped_entities.add(track_id)
                    snap_name = f"unauth_ID{track_id}_{now.strftime('%H%M%S')}.jpg"
                    save_path = os.path.join(UNAUTH_DIR, snap_name)
                    cv2.imwrite(save_path, full_crop)
                    send_alert_email_async(save_path, track_id, date_str, time_str, action_desc, breach_status)

                # Audit logging (1 row per sec per intruder)
                if current_time_sec - engine.last_logged_time[track_id] >= 1.0:
                    engine.last_logged_time[track_id] = current_time_sec
                    with open(config.LOG_FILE, mode="a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([date_str, time_str, f"ID_{track_id}", "UNAUTHORIZED", action_desc, breach_status, f"unauth_ID{track_id}_{now.strftime('%H%M%S')}.jpg"])

            # Visual bounding box & label
            cv2.rectangle(frame, (x1, y1), (x2, y2), status_color, 2)
            cv2.circle(frame, foot_coord, 5, status_color, -1)
            cv2.putText(frame, display_label, (x1, max(y1 - 10, 15)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, status_color, 2)

    # Top Status HUD
    hud_bg = frame.copy()
    cv2.rectangle(hud_bg, (0, 0), (frame.shape[1], 55), (20, 20, 20), -1)
    frame = cv2.addWeighted(hud_bg, 0.75, frame, 0.25, 0)

    clock_hud = f"{date_str} {time_str}"
    cv2.putText(frame, clock_hud, (frame.shape[1] - 210, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    if enrolled_face_hist is None:
        cv2.putText(frame, "SETUP MODE: Press 's' to enroll authorized admin face.", (15, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 165, 255), 2)
    else:
        status_msg = "PERIMETER: COMPROMISED (INTRUDER DETECTED)" if threat_active else "PERIMETER: SECURE"
        status_color = (0, 0, 255) if threat_active else (0, 255, 0)
        cv2.putText(frame, status_msg, (15, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

    cv2.imshow("Server Room Autonomous Vision System", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('s'):
        if current_boxes:
            target_box = current_boxes[0][0]
            target_id = current_boxes[0][1]
            head_crop = extract_head_region(frame, target_box)
            full_crop = frame[max(0, target_box[1]):min(frame.shape[0], target_box[3]),
                              max(0, target_box[0]):min(frame.shape[1], target_box[2])]
            if head_crop.size > 0:
                enrolled_face_hist = get_face_descriptor(head_crop)
                id_authorization.clear()
                id_match_scores.clear()
                # Explicitly lock this ID as authorized right away
                id_authorization[target_id] = True
                
                cv2.imwrite(os.path.join(AUTH_DIR, "authorized_admin.jpg"), full_crop)
                print(f"[+] Admin registered successfully! ID #{target_id} locked as AUTHORIZED.")
                winsound.Beep(1000, 200)
        else:
            print("[!] Step into frame and press 's'.")

cap.release()
cv2.destroyAllWindows()