# NTPC Safety Monitor: Multi-Camera PPE Detection System

An AI-based safety compliance monitoring Proof of Concept (PoC) designed to detect Personal Protective Equipment (PPE) violations at entry gates in real time. The system processes multiple camera streams, tracks workers, detects missing hardhats and safety vests, captures screenshots on confirmed violations, and serves reports and analytics via a web dashboard.

---

## System Requirements

- **Operating System**: Windows 10/11 or Ubuntu 20.04/22.04/24.04
- **Python**: v3.10 or higher
- **Node.js**: v18.0 or higher
- **Graphics Card**: Dedicated NVIDIA GPU (RTX 30-series / 40-series recommended) with CUDA support for real-time multi-stream performance.
- **RTSP Relay Server**: [MediaMTX](https://github.com/bluenviron/mediamtx/releases)

---

## Project Structure

```
├── .gsd/              # GSD project memory, plans, and state logs (local-only)
├── backend/           # FastAPI backend + YOLOv11 two-stage inference pipeline
├── dashboard/         # Next.js web portal (analytics, live streams, event logs)
├── docs/              # Presentation documentation
│   ├── ARCHITECTURE.md       # Threading model, pipeline diagrams, database schemas
│   ├── DEMO_SCRIPT.md        # Step-by-step walkthrough guide for live demos
│   └── DEPLOYMENT_PROPOSAL.md # Hardware specification, cost costing, and rollout plan
└── README.md          # Main setup and entry point guide
```

---

## Installation and Setup

### 1. RTSP Server Setup
1. Download the latest version of **MediaMTX** for your OS from [GitHub Releases](https://github.com/bluenviron/mediamtx/releases).
2. Extract the archive.
3. Run the executable (`mediamtx.exe` on Windows or `./mediamtx` on Linux) to start the server. It will listen on port `8554` for RTSP streams.

### 2. Python Backend Setup
1. Open a terminal in the project root.
2. Initialize and activate a virtual environment:
   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
   ```bash
   # Linux / Bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: This includes `ultralytics`, `fastapi`, `opencv-python`, `sqlalchemy`, and database drivers.*

### 3. Dashboard Setup
1. Open a new terminal in the `dashboard` directory:
   ```bash
   cd dashboard
   ```
2. Install npm packages:
   ```bash
   npm install --legacy-peer-deps
   ```
3. Create a `.env.local` file inside `dashboard/` with the API configurations (or leave defaults):
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

---

## Running the PoC

### Step 1: Start MediaMTX
Ensure `mediamtx` is running in the background.

### Step 2: Start the FastAPI Backend
From the project root (with the virtual environment active):
```bash
python -m uvicorn backend.app:app --reload --port 8000
```
This initializes the SQLite database (`backend/violations.db`), seeds default cameras (`cam_1` and `cam_2`), starts the background capture threads, and launches the API.

### Step 3: Start the Next.js Dashboard
From the `dashboard` directory:
```bash
npm run dev
```
Open your browser and navigate to [http://localhost:3000](http://localhost:3000) to view the live dashboard.

---

## Testing & Performance Benchmarks

To ensure the pipeline meets the requirements on local hardware, you can run the test and benchmark suites:

### 1. Run the Multi-Camera Integration Test
Verifies that the capture threads and inference loop successfully process 3 concurrent simulated streams without locking:
```bash
python backend/test_multi_camera.py
```

### 2. Run the Performance Benchmark
Measures total processed frames, combined throughput FPS, average latency, and PyTorch CUDA memory footprint:
```bash
python backend/benchmark_multi_camera.py
```

---

## Detailed Documentation

For in-depth reviews, consult the documents in the `docs/` folder:
- **[System Architecture](file:///c:/Users/ashmi/OneDrive/Documents/ntpc_vocational/docs/ARCHITECTURE.md)**: Details the multi-threaded ingestion model, state machine, and data flow diagrams.
- **[Demo Walkthrough Script](file:///c:/Users/ashmi/OneDrive/Documents/ntpc_vocational/docs/DEMO_SCRIPT.md)**: A step-by-step presentation script showing KPI cards, logs, filters, and offline simulator states.
- **[Production Rollout Proposal](file:///c:/Users/ashmi/OneDrive/Documents/ntpc_vocational/docs/DEPLOYMENT_PROPOSAL.md)**: Hardware selection, network topology, cabling specs, cost costing, and installation timeline.
