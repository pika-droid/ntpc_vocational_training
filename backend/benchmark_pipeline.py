# backend/benchmark_pipeline.py
import cv2
import time
import numpy as np
import torch
from inference_pipeline import TwoStagePPEPipeline

def run_benchmark(num_frames=50):
    print("--------------------------------------------------")
    print("NTPC PPE Violation Detection Pipeline Benchmark")
    print("--------------------------------------------------")
    
    # Initialize pipeline
    pipeline = TwoStagePPEPipeline()
    
    # Check CUDA
    if torch.cuda.is_available():
        print(f"CUDA Device: {torch.cuda.get_device_name(0)}")
        # Warmup GPU
        print("Warming up GPU...")
        warmup_frame = (np.random.rand(640, 640, 3) * 255).astype(np.uint8)
        for _ in range(5):
            _ = pipeline.process_frame(warmup_frame)
            
    # Generate mock frame sequence (simulate full HD CCTV resolution)
    print(f"Generating benchmark frames (1920x1080 resolution)...")
    frames = []
    for _ in range(num_frames):
        # We generate a blank image but draw some circles to simulate potential person shapes for YOLO
        img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        # Draw some mock shapes
        cv2.circle(img, (960, 540), 100, (255, 255, 255), -1)
        cv2.circle(img, (400, 300), 80, (255, 255, 255), -1)
        frames.append(img)
        
    print(f"Starting benchmark loop for {num_frames} frames...")
    start_time = time.time()
    
    for i, frame in enumerate(frames):
        t0 = time.time()
        _, viols = pipeline.process_frame(frame)
        latency = (time.time() - t0) * 1000
        if (i + 1) % 10 == 0 or i == 0:
            print(f"Frame {i+1}/{num_frames} processed. Latency: {latency:.2f}ms")
            
    end_time = time.time()
    total_duration = end_time - start_time
    avg_fps = num_frames / total_duration
    avg_latency = (total_duration / num_frames) * 1000
    
    print("\n--------------------------------------------------")
    print("BENCHMARK RESULTS:")
    print("--------------------------------------------------")
    print(f"Total Frames Processed: {num_frames}")
    print(f"Total Processing Time:  {total_duration:.2f} seconds")
    print(f"Average Frame Latency:  {avg_latency:.2f} ms")
    print(f"Average Throughput FPS: {avg_fps:.2f} FPS")
    print("--------------------------------------------------")
    
    if avg_fps >= 10.0:
        print("SUCCESS: Pipeline achieves the target of >= 10 FPS on local hardware!")
    else:
        print("WARNING: Pipeline runs below target 10 FPS. Check CUDA configuration.")
    print("--------------------------------------------------")

if __name__ == '__main__':
    run_benchmark()
