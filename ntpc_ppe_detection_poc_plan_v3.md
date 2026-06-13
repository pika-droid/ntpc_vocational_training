# NTPC PPE Violation Detection System: End-to-End PoC Plan (v3)

## 1. Project Summary

This project is a proof of concept for an AI-based safety monitoring system that uses live CCTV-like video streams to detect whether workers entering a plant gate are wearing mandatory PPE. The initial scope is limited to:

- **Helmet detection**
- **Safety jacket / safety vest detection**
- **Entry-gate monitoring**
- **Multi-camera support** using 2–3 Android phones as demo cameras
- **Violation screenshots** captured automatically when a rule breach is confirmed
- **Web dashboard** for logs, charts, and tables

The PoC is intended for an internship presentation / deployment proposal, with a technical focus and a path toward later plant integration.

---

## 2. Core Objective

The system must:

1. Ingest live video from multiple cameras.
2. Detect people entering a zone.
3. Crop the person region and run PPE detection on the crop.
4. Decide whether a worker is non-compliant.
5. Confirm a violation across a time window to reduce false alerts.
6. Capture and store a screenshot for each confirmed violation.
7. Store event metadata in a database.
8. Present violation logs and analytics in a web portal.

---

## 3. Scope and Assumptions

### In scope

- Proof of concept only
- 2–3 cameras
- Android phone cameras used as stand-ins for CCTV
- Live streaming
- Fixed gate-entry zone (no virtual line for PoC; full gate area treated as zone)
- One alert per entry
- Helmet and safety jacket only
- Charts, tables, and CSV export
- All inference and backend components run locally on the laptop (Intel 14700HX, 16 GB RAM, RTX 4070 8 GB)
- Database and object storage via Supabase (cloud-hosted, free tier) — this is the only cloud component
- Dashboard accessed over the local network during the demo; not publicly exposed
- Supervisor-level dashboard access (no authentication for PoC)

### Out of scope for the PoC

- Face recognition or identity tracking across days
- Access control integration
- Audio alarms
- Mobile app
- Manual review workflow
- Additional PPE classes such as gloves, shoes, goggles, or masks
- Video retention beyond screenshots
- Full production-grade multi-site deployment
- Virtual gate line per camera (deferred to real CCTV deployment)
- Stream reconnection / failure recovery (camera shown as offline on dashboard)
- Authentication
- Model fine-tuning on custom local data

---

## 4. Functional Requirements

### 4.1 Video Ingestion

- Accept live RTSP streams from multiple Android phones using the **IP Webcam** app (by Pavel Khlebovich).
- Route streams through **MediaMTX** as the RTSP relay.
- If a camera stream is unavailable, mark it as offline on the dashboard. No reconnection logic is required for the PoC.

### 4.2 Detection

- Detect **person** in the frame.
- On person detection, crop the person region.
- Run a PPE detector on the crop to detect:
  - helmet
  - safety vest / jacket
- Classify the person as:
  - compliant
  - helmet missing
  - vest missing
  - both missing

### 4.3 Violation Confirmation

A violation is triggered only if a tracked person remains **continuously non-compliant for at least 2 seconds**. If the person becomes compliant, or the track is lost for more than 1 second, the timer is reset.

Per-person state machine:

```
State: COMPLIANT or NON_COMPLIANT

On NON_COMPLIANT first detected:
    → start timer

If NON_COMPLIANT persists continuously for ≥ 2 seconds:
    → create violation event

If person becomes COMPLIANT:
    → reset timer

If track disappears for > 1 second:
    → reset timer
```

This approach is robust to inference FPS variation, brief occlusions, and intermittent tracking loss. One person generates only one alert per entry (enforced via tracking ID + cooldown).

### 4.4 Evidence Capture

- Save a screenshot for each confirmed violation.
- Store metadata: camera ID, zone, timestamp, violation type, and confidence score.
- Keep screenshots indefinitely for the PoC unless retention is changed later.

### 4.5 Analytics and Dashboard

- Show violation counts by:
  - camera
  - zone
  - hour
  - day
  - shift (configurable; see Section 11)
- Show tables and charts.
- Support CSV export of violation logs.
- Provide a live camera view (MJPEG snapshot feed) and a violation feed.

---

## 5. System Architecture

### High-level flow

```text
Android Phone Cameras (IP Webcam app)
        ↓
      RTSP
        ↓
     MediaMTX
        ↓
Inference Service
(YOLOv11 + Built-in Tracking + Rule Engine)
        ↓
Event Storage
(PostgreSQL + Object Storage for Screenshots)
        ↓
Web Dashboard
(Charts, tables, logs, MJPEG live feed)
```

### Concurrency model

The inference service uses the following threading model:

```text
Camera Thread 1 ──┐
Camera Thread 2 ──┼──▶ Frame Queue ──▶ Inference Thread ──▶ Event Queue ──▶ FastAPI (async)
Camera Thread 3 ──┘
```

- **One thread per camera** handles RTSP frame capture (I/O-bound; threads are appropriate).
- A **shared frame queue** decouples capture from inference.
- A **single inference thread** pulls frames from the queue and runs YOLO detection (GPU inference is serialized regardless).
- Results go into an **event queue** consumed by FastAPI async routes.

The target throughput is 10–15 FPS per stream across 2–3 cameras. Actual performance will be validated experimentally and depends on camera resolution, PPE detector size, and concurrent stream count. The RTX 4070 is expected to be sufficient for this workload.

### Rationale

This separation keeps the system modular:

- **Camera layer**: only handles streaming
- **Inference layer**: only handles AI and rule logic
- **Storage layer**: only stores events and screenshots
- **Presentation layer**: only displays results

This makes the PoC easier to build now and easier to replace with plant CCTV later.

---

## 6. Detection Pipeline

The implementation uses a **two-stage pipeline**. This is retained (rather than a single-stage model) because if the project is approved for deployment, the two-stage approach allows each stage to be tuned and replaced independently.

### Stage 1: Person Detection

A YOLOv11-based detector identifies people in the frame.

Outputs:
- bounding box for each person
- confidence score

### Stage 2: PPE Detection on Cropped Person Region

For each person crop:
- run a PPE detector
- detect helmet and vest
- infer compliance from spatial presence of these items in the crop

### Tracking

Use **Ultralytics' built-in tracking** (which wraps ByteTrack internally). This integrates with no additional dependencies via:

```python
model.track(source=frame, persist=True)
```

Tracking is needed to:
- prevent duplicate alerts
- associate multiple frames with one worker
- support the time-based confirmation window

---

## 7. Rule Logic

### Violation criteria

A violation is triggered if either of the following is missing:
- helmet
- safety jacket / vest

### Confirmation policy

Use a **time-based** confirmation window with the following per-person state machine:

```
State: COMPLIANT or NON_COMPLIANT

On NON_COMPLIANT first detected:
    → start timer

If NON_COMPLIANT persists continuously for ≥ 2 seconds:
    → create violation event

If person becomes COMPLIANT:
    → reset timer

If track disappears for > 1 second:
    → reset timer
```

The timer follows **continuous tracked presence**, not accumulated frames. This makes the logic robust to FPS variation, brief occlusions, and intermittent tracking loss, and is straightforward to defend during a presentation.

### Confidence thresholds

Confidence thresholds are **independently configurable per detector stage**. Initial default values:

| Stage | Default Threshold |
|---|---|
| Person detector | 0.50 |
| PPE detector | 0.50 |

Thresholds should be tuned after initial validation on live demo footage to balance false positives and false negatives. A single hard value across both stages is not appropriate, as person detection and PPE detection operate on different input scales and confidence distributions.

### Duplicate suppression

After a violation is created:
- do not create another violation for the same tracked person within a cooldown window
- default cooldown: **30 seconds**

### Zone evaluation

For the PoC, the full camera frame is treated as the gate zone. No virtual gate line or ROI is defined at this stage.

> **Limitation:** Using the entire frame as the detection zone may introduce occasional detections of individuals near — but not actively entering — the gate area, making analytics slightly less precise. This tradeoff is acceptable for a PoC and is deliberate: it reduces configuration complexity and avoids the need to define per-camera ROI coordinates without a stable camera setup. For production deployment, each camera will use a static virtual gate line defined once at installation time, since real CCTV positions are fixed.

---

## 8. Model Plan

### Recommended model family

Use **YOLOv11** as the primary detector family (via Ultralytics).

### Proposed model structure

#### Stage 1: Person detector

- Use the standard YOLOv11 COCO-pretrained model.
- The `person` class is already well-trained in COCO; no fine-tuning required for the PoC.

#### Stage 2: PPE detector

- Fine-tune a YOLOv11 model on public PPE datasets (see Section 9).
- Target classes: `helmet`, `no_helmet`, `vest`, `no_vest` (or equivalent class names depending on the chosen dataset).

### Why two-stage

A two-stage system is preferred for this project because:
- it is easier to explain in a technical proposal
- it can be tuned independently
- it can improve accuracy in gate scenes by reducing irrelevant background context
- it reduces unnecessary PPE inference on the whole frame
- it maps cleanly to the production architecture if the project is approved

### Training approach

1. Start with public PPE datasets (see Section 9).
2. Fine-tune the PPE detector on a merged dataset.
3. Evaluate against defined metrics.

> Note: Custom data collection and local fine-tuning are out of scope for the PoC.

### Model performance targets

The following are the minimum acceptable targets for a credible PoC demo:

| Metric | Target |
|---|---|
| mAP@50 (helmet + vest classes) | ≥ 0.70 |
| Precision | ≥ 0.75 |
| Recall | ≥ 0.70 |
| Inference speed (RTX 4070, per stream) | ≥ 10 FPS |

Precision is weighted slightly higher than recall to minimize false alarms during the demo.

---

## 9. Dataset Strategy

### Recommended datasets

The following public datasets are suitable for training the PPE detector. All are available in YOLO format (via Roboflow, Kaggle, or direct download):

| Dataset | Source | Notes |
|---|---|---|
| **Hard Hat Workers** (Joseph Nelson) | Roboflow Universe | Most widely used; helmet classes |
| **Construction Site Safety** | Roboflow Universe | Helmet + vest + person |
| **PPE Detection Dataset** | Roboflow Universe | Multiple community versions |
| **SHWD** (Safety Helmet Wearing Dataset) | Academic / GitHub | Good quality, helmet-focused |
| **CHV Dataset** (Construction Helmet & Vest) | Academic | Helmet and vest together |
| **Safety Helmet Detection** | Kaggle | Several versions available |
| **Open Images v7** | Google | Contains `helmet` class; large scale |
| **PISC** (Person in Safety Clothing) | Academic | Vest-focused |

### Recommended strategy

1. Start with Roboflow Universe datasets (they export directly in YOLO format).
2. Merge compatible datasets with consistent class labels.
3. Capture a small set of sample frames from the demo phones.
4. Use these frames as a calibration set — not for retraining, but to evaluate whether the model generalises and to guide threshold tuning.
5. Adjust per-stage confidence thresholds based on observed false positive / false negative rates on the calibration frames.

> This is not full fine-tuning (which remains out of scope), but a lightweight calibration step that significantly improves demo reliability without requiring labelled data or retraining.

### Why this matters

Public datasets help get the pipeline working quickly, but local footage often requires threshold tuning because camera angles, lighting, and clothing styles differ from dataset images. A small calibration set from the demo phones addresses this without the overhead of a full custom training run.

---

## 10. Backend and Storage

### Backend

Use a **Python / FastAPI** backend to expose APIs for:
- camera management
- violation listing
- analytics
- health checks

### Database

Use **PostgreSQL** for:
- camera metadata
- violation metadata
- timestamps
- zone information
- confidence scores

PostgreSQL is retained (over SQLite) because if this project is approved for deployment, the database layer will not need to be replaced.

### Screenshot storage

Use **object storage** for screenshots rather than storing them directly in database rows.

A Supabase-like stack is reasonable for the PoC (free tier) because it provides:
- PostgreSQL for metadata
- object storage for screenshots

Object storage is retained for the same reason as PostgreSQL — it maps directly to the production pattern.

### Storage pattern

- Database stores metadata and screenshot URLs.
- Object storage holds the screenshot files.

---

## 11. Analytics Plan

Analytics are event-driven — the system aggregates confirmed violations after detection.

### Shift definitions

Shift windows are **configurable** and stored as named time ranges in the database or a config file. The system tags each violation event with the active shift at the time of detection.

For the PoC, example shift windows are used as placeholders. Production deployments would use actual plant shift schedules provided by NTPC operations.

| Shift | Example Hours |
|---|---|
| Morning | 09:00 – 13:00 |
| Evening | 15:00 – 19:00 |
| Outside shift | All other hours |

### Required analytics

- violations by camera
- violations by zone
- violations by time of day
- violations by shift (configurable windows; see Section 11)
- daily violation totals
- helmet-missing vs vest-missing counts
- trend over time

### Visual outputs

- line charts
- bar charts
- summary cards
- tables
- CSV export

### Example dashboard views

- total violations today
- active cameras
- violations by gate
- top violation periods
- violation log table with screenshots

---

## 12. Web Portal Plan

### Main pages

#### Dashboard
- summary cards
- trend charts
- recent violations

#### Live View
- MJPEG snapshot feed per camera
- live status indicators (online / offline)
- recent alert markers

> **Note:** The MJPEG feed is a lightweight monitoring preview, not a full live stream. It is appropriate for a PoC dashboard where the goal is situational awareness, not continuous video review. Production deployments would expose RTSP, HLS, or WebRTC streams for full live viewing.

#### Violation Log
- timestamp
- camera
- zone
- violation type
- confidence score
- screenshot preview

#### Analytics
- charts and tables
- filters by camera, zone, date, and shift
- CSV export

### User role

For the PoC, a single supervisor-level view is sufficient. No authentication is required at this stage.

---

## 13. Deployment Plan

### Hosting model

The deployment is split as follows:

| Component | Hosting |
|---|---|
| RTSP relay (MediaMTX) | Local laptop |
| Inference service (FastAPI + YOLO) | Local laptop |
| Database (PostgreSQL) | Supabase free tier (cloud) |
| Object storage (screenshots) | Supabase free tier (cloud) |
| Dashboard (React / Next.js) | Local laptop, served over local network |

This is a deliberate choice. Continuous multi-stream GPU inference is not practical on a free cloud VM. Supabase handles the only components that genuinely benefit from cloud hosting (persistent storage and the database). The dashboard is accessed over the local network during the demo and is not publicly exposed.

```
Hardware (inference):
- Intel Core i9-14700HX
- 16 GB RAM
- NVIDIA RTX 4070 (8 GB VRAM)
```

### Target performance

- 2–3 RTSP streams at 10–15 FPS per stream

Actual throughput will be measured during system validation. Performance depends on camera resolution, PPE detector variant size (e.g., YOLOv11n vs YOLOv11s), and concurrent stream count. The RTX 4070 is expected to be sufficient for the target workload, but this will be confirmed experimentally before the final demo.

### Path to production

The architecture is designed so that replacing the laptop with an on-premise inference server or cloud GPU VM requires only configuration changes, not structural ones.

---

## 14. Recommended Build Sequence

### Phase 1: Single-camera prototype + Docker setup

- Set up Docker Compose with all services (FastAPI, PostgreSQL, MediaMTX)
- Connect one Android phone via RTSP using IP Webcam app
- Run person detection
- Run PPE detection
- Confirm a violation using the time-based window
- Save one screenshot
- Show a simple event log

> Docker is set up in Phase 1 so the development environment matches the final deployment from the start.

### Phase 2: Multi-camera support

- Connect 2–3 cameras
- Assign a unique camera ID and zone to each
- Implement the capture thread per camera + shared frame queue
- Ensure each camera has independent event logs

### Phase 3: Tracking and duplicate suppression

- Add Ultralytics built-in tracking
- Add multi-frame (time-based) confirmation
- Enforce one alert per entry using track ID + cooldown

### Phase 4: Dashboard and analytics

- Build the web portal (React or Next.js)
- Add MJPEG snapshot feed for live view
- Add tables and charts
- Add shift-based analytics (configurable shift windows)
- Add CSV export

### Phase 5: Cleanup and presentation polish

- Improve labels and screenshots
- Add deployment diagrams
- Prepare a demo script
- Prepare a short architecture summary for presentation

---

## 15. Risks and Constraints

### Risk 1: Camera placement

If the camera is too far from workers, PPE objects may be too small to detect reliably. Phones should be positioned at roughly 2–4 metres from the entry point.

### Risk 2: Motion blur and low light

Video quality will strongly affect detection. Ensure adequate lighting for the demo environment.

### Risk 3: False alerts

Mitigated by the time-based confirmation window (2 seconds) and per-stage confidence thresholds (default 0.50 for each stage, tunable after validation).

### Risk 4: Local domain shift

A model trained only on public datasets may underperform in the specific demo environment. Threshold tuning after initial testing is recommended before the final demo.

### Risk 5: Dataset label inconsistency

Merging multiple public datasets may introduce inconsistent class names (e.g., `hardhat` vs `helmet`). A label normalization step is required before training.

---

## 16. Deliverables

The final PoC should produce:

1. A working live demo with 2–3 phone cameras
2. A PPE detection pipeline (two-stage: person + PPE)
3. Violation screenshot capture
4. A backend database of events (PostgreSQL)
5. A dashboard with logs and charts (including shift analytics)
6. CSV export of violation records
7. A technical architecture document
8. A deployment proposal summary

---

## 17. Technology Stack

### Video and inference
- **IP Webcam** (Android app by Pavel Khlebovich) — RTSP source
- **MediaMTX** — RTSP relay / server
- **OpenCV** — frame capture
- **YOLOv11** (Ultralytics) — person + PPE detection
- **Ultralytics built-in tracking** (ByteTrack wrapper) — track ID management

### Backend
- **FastAPI** — API layer (async)
- **PostgreSQL** — event and metadata storage
- **Supabase** (or equivalent) — object storage for screenshots

### Frontend
- **Next.js or React** — dashboard
- **Recharts or Chart.js** — charts
- **TanStack Table** (or similar) — violation log table
- **CSV export utility** — built-in or `papaparse`

### Packaging
- **Docker Compose** — all services containerized from Phase 1

---

## 18. Summary

The project is best treated as a modular safety analytics platform with a live PPE detection pipeline at the front and a reporting portal at the back.

The PoC should prove four things:

1. Live multi-camera video ingestion works.
2. PPE violations can be detected reliably enough for demonstration (mAP@50 ≥ 0.70).
3. Screenshots can be captured automatically on confirmed violations.
4. Analytics can summarize violations by zone, shift, and time.

That is sufficient for a strong internship proposal and a credible foundation for later plant integration.
