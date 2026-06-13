# Presentation Walkthrough Demo Script: NTPC Safety Monitor

This document outlines the step-by-step demonstration script for presenting the NTPC PPE Detection PoC system to supervisors, evaluators, and stakeholders.

---

## Scenario 1: Setup and System Initialization

### Objective
Demonstrate that the system starts up cleanly and reports health parameters.

1. **Start MediaMTX Relay Server**:
   Double click `mediamtx.exe` (or run it via cmd) to start the RTSP streaming server on port 8554.

2. **Start FastAPI Backend Server**:
   Open a terminal and run the backend using the virtual environment:
   ```bash
   .venv\Scripts\python -m uvicorn backend.app:app --reload --port 8000
   ```
   *Verify in logs*:
   - Database schemas initialized.
   - Default cameras (`cam_1` and `cam_2`) seeded.
   - Inference loop thread started.
   - Event processing worker active.

3. **Start Next.js Dashboard**:
   Open a new terminal and run:
   ```bash
   npm run dev --prefix dashboard
   ```
   Open a browser and navigate to `http://localhost:3000`.

---

## Scenario 2: Dashboard Overview & Real-Time Alerts

### Objective
Showcase the supervisor's main landing page, KPI summaries, and live alert ticker.

1. **Verify KPI Cards**:
   - Point out the four summary cards: **Total Violations**, **Active Cameras**, **No Helmet Logs**, and **No Safety Vest Logs**.
   - Explain that these metrics are fetched dynamically from the FastAPI backend and updated periodically.

2. **Demonstrate Connection Status**:
   - Stop the backend server temporarily to show the red **Connection Alert** banner appear at the top.
   - Start the backend server again and observe the banner disappear automatically within 3 seconds.

3. **Observe Live Alert Ticker**:
   - Point to the **Real-time Violation Feed** in the center.
   - As the backend processes streams, new confirmed violation items will fade in at the top of the list.
   - Explain the violation confirmation logic (needs 2 seconds of continuous violation, preventing false alarms from camera noise).

4. **Interactive Screenshot Zoom**:
   - Click on the crop thumbnail of any logged violation.
   - Point out the modal dialog that displays the high-resolution annotated screenshot with glowing red/orange borders outlining the worker's bounding box.
   - Click the **X** button to close the modal.

---

## Scenario 3: Live Video Streams Page

### Objective
Showcase real-time monitoring capability and camera offline states.

1. **Navigate to "Live Streams"** via the sidebar.
2. **Review Feed Grid**:
   - Observe the live MJPEG preview tiles for the configured cameras.
   - Point out the pulsing **Green Indicator** showing cameras are online.
3. **Simulate Offline Event**:
   - Manually delete a camera configuration, or point a camera to an invalid URL.
   - Notice that the feed changes immediately to a dark grey card showing **CAMERA OFFLINE** in red letters, with a pulsing red status indicator.
   - This proves the system is resilient and informs the supervisor immediately if physical CCTV cameras go dark.

---

## Scenario 4: Camera Configuration Panel (CRUD)

### Objective
Demonstrate administrative flexibility to add, update, or remove cameras on the fly.

1. **Navigate to "Camera Config"** in the sidebar.
2. **Add a New Camera**:
   - Click the **Add Camera** button (or open the creation panel).
   - Enter details:
     - **Camera ID**: `cam_3`
     - **RTSP URL**: `backend/test_video_1.mp4` (simulate stream via file) or a local webcam ID like `0`.
     - **Zone**: `Main Gate Ingest`
   - Submit the form.
3. **Verify Addition**:
   - Check the cameras table list to confirm `cam_3` is added.
   - Navigate back to **Live Streams** to confirm a new video grid card is dynamically created for `cam_3`.
4. **Delete the Camera**:
   - Go back to **Camera Config**.
   - Click **Delete** on `cam_3`.
   - Confirm it is removed from the table and grid.

---

## Scenario 5: Historical Logs & CSV Export

### Objective
Show how supervisors search, audit, and export safety violations.

1. **Navigate to "Violation Logs"** in the sidebar.
2. **Demonstrate Filters**:
   - Use the **Camera ID** dropdown to show only violations from `cam_1`.
   - Use the **Violation Type** filter to isolate `helmet_missing` infractions.
   - Filter by **Shift** (e.g. morning, afternoon, night) to demonstrate compliance tracking per team shift.
3. **Export to CSV**:
   - Click the **Export to CSV** button.
   - Open the downloaded CSV file in Excel/Notepad.
   - Point out that all filtered metadata fields (ID, Camera, Zone, Timestamp, Type, Confidence, Shift) are exported perfectly for external reporting.

---

## Scenario 6: Compliance Analytics Visualisation

### Objective
Show off the premium analytics dashboard for high-level management audits.

1. **Navigate to "Compliance Analytics"** in the sidebar.
2. **Review Charts**:
   - **Trend Chart (Area Chart)**: Highlights violation frequencies over time.
   - **Camera & Zone Distribution (Bar Charts)**: Visualizes which location or camera registers the highest number of infractions.
   - **Infraction Type Chart (Pie Chart)**: Breaks down the percentage of helmet vs vest vs combined violations.
   - **Shift Analysis (Pie/Bar)**: Shows which shift is most/least compliant.
3. **Explain Value**:
   - Explain how plant managers can use these charts to allocate safety officers to high-infraction zones or adjust training sessions for non-compliant shifts.

---

## Scenario 7: Performance Benchmark Check

### Objective
Prove that the system meets the high-performance throughput requirement on the local edge hardware.

1. **Run the Multi-Camera Benchmark**:
   In a terminal, execute:
   ```bash
   .venv\Scripts\python backend/benchmark_multi_camera.py
   ```
2. **Present Results**:
   - Show that the combined throughput is **~40–60 FPS** on local hardware.
   - Point out the low latency (**~50–80 ms** per frame).
   - Show the GPU memory usage footprint (**~105 MB**), proving the system has a lightweight footprint and can easily scale to support 6–8 concurrent entry cameras on a single RTX 4070.
