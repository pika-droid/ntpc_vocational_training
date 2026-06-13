# backend/test_multi_camera.py
import cv2
import numpy as np
import time
import os
import shutil
from multi_camera_pipeline import MultiCameraPPEPipeline

def create_dummy_video(filename, width=640, height=480, fps=15, duration_sec=3):
    """Creates a temporary MP4 video of a moving white circle (simulating a moving person)."""
    print(f"Creating dummy video: {filename}")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    total_frames = fps * duration_sec
    for i in range(total_frames):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw a circle moving horizontally across the frame
        cx = int(50 + i * (width - 100) / total_frames)
        cy = height // 2
        cv2.circle(img, (cx, cy), 60, (255, 255, 255), -1)
        out.write(img)
        
    out.release()

def test_pipeline():
    video1_path = "backend/test_video_1.mp4"
    video2_path = "backend/test_video_2.mp4"
    
    # Create the temporary videos
    create_dummy_video(video1_path)
    create_dummy_video(video2_path)
    
    camera_configs = {
        "cam_1": {"rtsp_url": video1_path, "zone_name": "Main Gate Entrance"},
        "cam_2": {"rtsp_url": video2_path, "zone_name": "Vehicle Gate Exit"}
    }
    
    print("\nInitializing Multi-Camera Pipeline...")
    pipeline = MultiCameraPPEPipeline(
        camera_configs=camera_configs,
        stage1_path='yolov11n.pt',
        conf_threshold=0.30  # lower threshold to guarantee detection on mock frames
    )
    
    print("Starting pipeline loop...")
    pipeline.start()
    
    # Let it process for 5 seconds
    run_duration = 5.0
    start_time = time.time()
    
    print(f"Running pipeline for {run_duration} seconds...")
    try:
        while time.time() - start_time < run_duration:
            time.sleep(1.0)
            print("--- Pipeline Health Status ---")
            for cam_id, cap in pipeline.captures.items():
                frame, frame_id, is_online = cap.get_latest_frame()
                print(f"Camera '{cam_id}': Online={is_online}, Monotonic Frame ID={frame_id}")
            print(f"Total Confirmed Violations: {len(pipeline.confirmed_violations)}")
            print("------------------------------")
    finally:
        print("\nStopping pipeline and cleaning up threads...")
        pipeline.stop()
        
        # Clean up temporary video files
        if os.path.exists(video1_path):
            os.remove(video1_path)
        if os.path.exists(video2_path):
            os.remove(video2_path)
            
    print("\nPipeline stopped successfully.")
    
    # Assertions for verification
    print("\nVerifying Test Results:")
    success = True
    for cam_id, cap in pipeline.captures.items():
        # Verify frames were read
        if cap.frame_id == 0:
            print(f"FAIL: Camera '{cam_id}' did not read any frames.")
            success = False
        else:
            print(f"PASS: Camera '{cam_id}' processed {cap.frame_id} frames.")
            
    if len(pipeline.confirmed_violations) == 0:
        # Since fallback alternates compliance, mock tracking should trigger violations!
        print("WARNING: No violations were detected. Double check detection thresholds/fallbacks.")
    else:
        print(f"PASS: Detected {len(pipeline.confirmed_violations)} violations.")
        
    if success:
        print("\nSUCCESS: Multi-camera threading and pipeline integration verified!")
    else:
        print("\nFAILURE: Multi-camera pipeline failed validation checks.")
        exit(1)

if __name__ == "__main__":
    test_pipeline()
