# backend/app.py
import os
import sys
import time
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import cv2

# Ensure backend directory is in path
sys.path.append(os.path.dirname(__file__))

from database import DatabaseManager
from storage import StorageManager
from multi_camera_pipeline import MultiCameraPPEPipeline
from event_processor import EventProcessorWorker

# Initialize global managers
db_manager = DatabaseManager()
storage_manager = StorageManager()
pipeline = None
event_worker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pipeline, event_worker
    print("[Lifespan] Starting up application...")
    
    # 1. Initialize DB tables
    db_manager.init_db()
    
    # 2. Load camera configs from DB
    db_cameras = db_manager.get_cameras()
    
    # Seed default cameras for PoC if DB is empty
    if not db_cameras:
        print("[Lifespan] Seeding default cameras...")
        db_manager.upsert_camera("cam_1", "0", "Main Gate Entrance")
        db_manager.upsert_camera("cam_2", "1", "Vehicle Gate Exit")
        db_cameras = db_manager.get_cameras()
        
    camera_configs = {
        cam["id"]: {"rtsp_url": cam["rtsp_url"], "zone_name": cam["zone_name"]}
        for cam in db_cameras
    }
    
    # 3. Initialize pipeline and background event processor
    pipeline = MultiCameraPPEPipeline(camera_configs=camera_configs)
    pipeline.start()
    
    event_worker = EventProcessorWorker(
        event_queue=pipeline.event_queue,
        db_manager=db_manager,
        storage_manager=storage_manager
    )
    event_worker.start()
    
    # Run a background thread to periodically update camera online status in the DB
    def update_camera_statuses():
        while not pipeline.stopped:
            try:
                for cam_id in list(pipeline.camera_configs.keys()):
                    with pipeline.lock:
                        cap = pipeline.captures.get(cam_id)
                    if cap:
                        db_manager.update_camera_status(cam_id, cap.is_online)
            except Exception as e:
                print(f"[Lifespan] Error updating camera status: {e}")
            time.sleep(5.0)
            
    status_thread = threading.Thread(target=update_camera_statuses, daemon=True)
    status_thread.start()
    
    yield
    
    print("[Lifespan] Shutting down application...")
    if event_worker:
        event_worker.stop()
    if pipeline:
        pipeline.stop()

# Initialize FastAPI application
app = FastAPI(
    title="NTPC PPE Detection Dashboard API",
    description="FastAPI backend for multi-camera safety compliance and violation tracking",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount screenshots directory to serve local images
static_screenshots_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_screenshots_path), name="static")

@app.get("/api/health")
def health_check():
    active_cameras = 0
    if pipeline:
        with pipeline.lock:
            active_cameras = len(pipeline.camera_configs)
            
    return {
        "status": "healthy",
        "database_type": db_manager.db_type,
        "active_cameras_pipeline": active_cameras,
        "storage_mode": "Supabase" if storage_manager.supabase else "Local static files"
    }

# Camera CRUD API
@app.get("/api/cameras")
def get_cameras():
    try:
        return db_manager.get_cameras()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cameras")
def add_or_update_camera(camera: dict):
    cam_id = camera.get("id")
    rtsp_url = camera.get("rtsp_url")
    zone_name = camera.get("zone_name")
    
    if not cam_id or not rtsp_url or not zone_name:
        raise HTTPException(status_code=400, detail="Missing required fields: id, rtsp_url, zone_name")
        
    try:
        db_manager.upsert_camera(cam_id, rtsp_url, zone_name)
        if pipeline:
            pipeline.add_camera(cam_id, rtsp_url, zone_name)
        return {"message": f"Camera '{cam_id}' upserted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/cameras/{cam_id}")
def delete_camera(cam_id: str):
    try:
        db_manager.delete_camera(cam_id)
        if pipeline:
            pipeline.remove_camera(cam_id)
        return {"message": f"Camera '{cam_id}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Violations API
@app.get("/api/violations")
def get_violations(
    camera_id: str = Query(None),
    zone: str = Query(None),
    violation_type: str = Query(None),
    shift: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    try:
        return db_manager.get_violations(
            camera_id=camera_id,
            zone=zone,
            violation_type=violation_type,
            shift=shift,
            start_date=start_date,
            end_date=end_date
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Summary API
@app.get("/api/analytics/summary")
def get_analytics():
    try:
        summary = db_manager.get_analytics_summary()
        
        # Add active camera count dynamically from pipeline
        active_cams_count = 0
        if pipeline:
            with pipeline.lock:
                active_cams_count = sum(1 for cap in pipeline.captures.values() if cap.is_online)
                
        summary["active_cameras_count"] = active_cams_count
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# MJPEG live preview stream
@app.get("/api/cameras/{cam_id}/stream")
def camera_stream(cam_id: str):
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
        
    with pipeline.lock:
        exists = cam_id in pipeline.camera_configs
        
    if not exists:
        raise HTTPException(status_code=404, detail=f"Camera '{cam_id}' not found")
        
    def generate():
        while True:
            with pipeline.lock:
                cap = pipeline.captures.get(cam_id)
                frame = pipeline.latest_processed_frames.get(cam_id)
                
            is_online = cap.is_online if cap else False
            
            if is_online and frame is not None:
                success, jpeg = cv2.imencode('.jpg', frame)
                if success:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
            else:
                # Return black screen with Camera Offline message
                offline_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(
                    offline_frame,
                    f"CAMERA {cam_id} OFFLINE",
                    (120, 240),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )
                success, jpeg = cv2.imencode('.jpg', offline_frame)
                if success:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                    
            time.sleep(0.1)  # Limit stream output to ~10 FPS to save bandwidth
            
    return StreamingResponse(
        generate(), 
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
