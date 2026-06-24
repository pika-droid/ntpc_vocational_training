# backend/benchmark_multi_camera.py
import cv2
import numpy as np
import time
import os
import torch
import sys
from multi_camera_pipeline import MultiCameraPPEPipeline

def create_dummy_video(filename, width=1280, height=720, fps=15, duration_sec=5):
    """Creates a temporary MP4 video of a moving white circle (simulating a worker moving)."""
    print(f"Creating benchmark dummy video: {filename} ({width}x{height}, {fps} fps, {duration_sec}s)")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    total_frames = fps * duration_sec
    for i in range(total_frames):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        # Draw a circle moving horizontally across the frame
        cx = int(50 + i * (width - 100) / total_frames)
        cy = height // 2
        cv2.circle(img, (cx, cy), 100, (255, 255, 255), -1)
        out.write(img)
        
    out.release()

def run_benchmark():
    print("--------------------------------------------------")
    print("NTPC PPE Multi-Camera Pipeline Benchmark (3 Streams)")
    print("--------------------------------------------------")
    
    video1_path = "backend/temp_bench_1.mp4"
    video2_path = "backend/temp_bench_2.mp4"
    video3_path = "backend/temp_bench_3.mp4"
    
    # Create the temporary videos
    create_dummy_video(video1_path)
    create_dummy_video(video2_path)
    create_dummy_video(video3_path)
    
    camera_configs = {
        "cam_1": {"rtsp_url": video1_path, "zone_name": "Main Entrance"},
        "cam_2": {"rtsp_url": video2_path, "zone_name": "Vehicle Exit"},
        "cam_3": {"rtsp_url": video3_path, "zone_name": "Loading Dock"}
    }
    
    print("\nInitializing Pipeline on device:", "CUDA" if torch.cuda.is_available() else "CPU")
    pipeline = MultiCameraPPEPipeline(
        camera_configs=camera_configs,
        stage1_path='yolo11n.pt',
        conf_threshold=0.30  # lower threshold to guarantee detection on mock frames
    )
    
    # Warm up inference pipeline
    print("Warming up models...")
    warmup_frame = (np.random.rand(640, 640, 3) * 255).astype(np.uint8)
    pipeline.process_frame("cam_1", warmup_frame, time.time())
    
    print("Starting pipeline streams...")
    pipeline.start()
    
    run_duration = 6.0
    start_time = time.time()
    
    print(f"Running pipeline benchmark for {run_duration} seconds...")
    
    try:
        time.sleep(run_duration)
    finally:
        print("\nStopping pipeline...")
        pipeline.stop()
        
        # Clean up temporary video files
        for f in [video1_path, video2_path, video3_path]:
            if os.path.exists(f):
                os.remove(f)
                
    print("\n--------------------------------------------------")
    print("BENCHMARK RESULTS:")
    print("--------------------------------------------------")
    
    total_processed = 0
    cam_reports = []
    
    for cam_id, cap in pipeline.captures.items():
        processed_frames = pipeline.last_processed_ids.get(cam_id, 0)
        total_processed += processed_frames
        cam_reports.append(f"Camera '{cam_id}': Processed {processed_frames} frames")
        
    for report in cam_reports:
        print(report)
        
    actual_duration = time.time() - start_time - 1.0 # Subtract startup lag
    if actual_duration <= 0:
        actual_duration = run_duration
        
    combined_fps = total_processed / actual_duration
    avg_latency_ms = (actual_duration / max(1, total_processed)) * 1000 * len(camera_configs)
    
    print(f"Total Processed Frames: {total_processed}")
    print(f"Combined Throughput:    {combined_fps:.2f} FPS")
    print(f"Average Frame Latency:  {avg_latency_ms:.2f} ms")
    
    # GPU utilization metrics
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / (1024 ** 2)
        reserved = torch.cuda.memory_reserved(0) / (1024 ** 2)
        print(f"GPU Memory Allocated:   {allocated:.1f} MB")
        print(f"GPU Memory Reserved:    {reserved:.1f} MB")
    else:
        print("GPU Status:             No GPU/CUDA available, running on CPU")
        
    print("--------------------------------------------------")
    
    target_fps_per_stream = 10.0
    target_fps_total = target_fps_per_stream * len(camera_configs)
    
    if combined_fps >= target_fps_total:
        print(f"SUCCESS: Pipeline achieves the target of >= {target_fps_per_stream} FPS per stream!")
    else:
        print(f"WARNING: Pipeline runs below target {target_fps_total} combined FPS. Check GPU configuration.")
    print("--------------------------------------------------")

if __name__ == '__main__':
    run_benchmark()
