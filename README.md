# Autonomous Vision & Behaviour Understanding System
**Problem Statement:** HNX26PSI07  
**Track:** Workplace Safety, Behavior Understanding & Secure Facility Surveillance  
**Execution Profile:** Edge-Native (Runs locally on standard CPU/Webcam at 30 FPS, Zero Cloud Latency)

---

## 📌 Executive Summary
Standard CCTV infrastructure is fundamentally passive: it records historical video or issues context-blind alerts on generic motion without resolving key forensic questions: **Who is inside? What actions are being performed across time? Is the behavior compliant, suspicious, or dangerous?**

This project delivers an **Edge-Deployable Autonomous Vision & Behavioral Audit System** engineered for high-security facilities such as Restricted Server Vaults, Nuclear Containment Zones, and Industrial Cleanrooms. Running entirely on local CPU hardware at 30 FPS, the pipeline integrates **temporal multi-object tracking**, **ground-contact perimeter defense**, **zero-dependency biometric clearance**, **posture analysis**, **kinetic motion-based assault detection**, and **asynchronous multi-modal incident escalation**.

---

## 🚀 System Architecture & Capabilities

### 1. Spatial Tracking & Identity Persistence
* **Detector:** Ultralytics YOLOv8-nano fine-tuned for high-speed person detection.
* **Tracker:** ByteTrack with Kalman filtering and Hungarian data association. It maintains stable entity identities (such as ID #1 and ID #2) across frames, trajectory overlaps, and temporary camera occlusions.

### 2. Geometric Perimeter Defense (Foot-Contact Polygon Testing)
* Traditional systems track bounding box centers, causing perspective errors and false alarms when a person merely leans forward.
* This engine anchors each person directly to their **ground-contact foot coordinates** (the bottom-center of the bounding box).
* Boundary inclusion within a customizable restricted zone polygon is checked deterministically using ray casting to confirm whether the person's feet have actually crossed into the restricted vault floor.

### 3. Kinematic Posture & Loitering Analysis
* **Movement Tracking:** Evaluates physical displacement over time. If a person stays within the same small radius for longer than 5 seconds, the system flags their behavior as **Suspicious Loitering**.
* **Posture Classification:** Compares bounding box width against height:
  * When stationary and compressed in height, the person is classified as **Sitting or Crouching**.
  * When stationary and vertically upright, the person is classified as **Standing Still**.
  * When continuously shifting coordinates across frames, the person is classified as **Moving or Walking**.

### 4. Advanced Motion Detection & Public Assault Analysis
* Simple pixel-based motion detectors fail in public spaces because wind, shadows, or background objects cause constant false alarms.
* Our system implements an **Inter-Entity Kinetic Motion Detector**:
  * **Proximity Check:** Continuously monitors the physical distance between all detected individuals. Physical altercations can only happen when two entities enter intimate striking distance.
  * **Turbulence & Acceleration Analysis:** When two people are in close contact, the system monitors rapid, erratic spikes in velocity and sudden bounding box shifts (characteristic of pushing, grappling, thrashing, or striking).
  * **Intelligent Escalation:** While smooth movement indicates normal conversation or walking past each other, high kinetic turbulence at close range immediately triggers a **Critical Violence / Assault Alert**.

### 5. Zero-Dependency In-Memory Biometric Verification
* Avoids heavy external C++ dependencies or cloud biometrics.
* Enrolls the authorized administrator in memory on keypress ('s') by extracting a combined color distribution and structural intensity descriptor from the upper head region.
* Uses sticky identity memory to lock verified administrators in **Green (ADMIN)** while immediately flagging unverified faces in **Red (UNAUTHORIZED)**.
* Face templates exist strictly in RAM—restarting the application resets all credentials for a clean setup demonstration.

### 6. Multi-Modal Escalation & Forensic Auditing
* **Acoustic & Spoken Alarm:** Plays a dual-tone industrial siren and speaks voice warnings on local edge speakers.
* **Forensic Evidence Capture:** Auto-crops high-resolution intruder mugshots and altercation scenes directly into dedicated evidence folders.
* **Background Email Reporting:** Dispatches SSL-encrypted emails with attached incident snapshots, exact local timestamps, activity classifications, and perimeter statuses without freezing the live video.
* **Immutable Audit Trail:** Logs structured security records into a CSV file for forensic review.

---

## 🛠️ Tech Stack

* **Computer Vision & Tracking:** Ultralytics YOLOv8-nano, ByteTrack, OpenCV
* **Kinematics & Geometry:** NumPy
* **Alerting & Escalation:** winsound, pyttsx3 (offline Windows speech engine)
* **Secure Messaging:** Python smtplib, email.message (SSL encrypted)
* **Concurrency:** Python threading (ensures non-blocking email alerts while maintaining 30 FPS video)

---
