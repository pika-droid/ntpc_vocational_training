# backend/camera_capture.py
import cv2
import time
import threading
import os

class CameraCapture:
    def __init__(self, camera_id, rtsp_url, zone_name="default_zone"):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.zone_name = zone_name
        
        # Thread safety variables
        self.lock = threading.Lock()
        self.latest_frame = None
        self.frame_id = 0
        self.is_online = False
        
        # Thread control
        self.stopped = False
        self.thread = None
        
        # Start capture thread
        self.start()

    def start(self):
        self.stopped = False
        # If rtsp_url is a digit (like "0"), convert it to an integer for local webcam support
        if isinstance(self.rtsp_url, str) and self.rtsp_url.isdigit():
            self.source = int(self.rtsp_url)
        else:
            self.source = self.rtsp_url
            
        self.thread = threading.Thread(target=self._capture_loop, name=f"Cam-{self.camera_id}", daemon=True)
        self.thread.start()

    def _capture_loop(self):
        print(f"[Camera {self.camera_id}] Starting capture thread for source: {self.source}")
        
        cap = None
        while not self.stopped:
            if cap is None or not cap.isOpened():
                print(f"[Camera {self.camera_id}] Connecting to source: {self.source}")
                cap = cv2.VideoCapture(self.source)
                # Set a low buffer size for RTSP to minimize latency
                if isinstance(self.source, str) and self.source.startswith("rtsp"):
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                if not cap.isOpened():
                    print(f"[Camera {self.camera_id}] Failed to open source. Retrying in 5 seconds...")
                    with self.lock:
                        self.is_online = False
                    time.sleep(5.0)
                    continue

            ret, frame = cap.read()
            if not ret:
                if isinstance(self.source, str) and not self.source.startswith("rtsp") and os.path.exists(self.source):
                    # Loop video files
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        print(f"[Camera {self.camera_id}] Failed to loop video file. Reconnecting...")
                        with self.lock:
                            self.is_online = False
                        cap.release()
                        cap = None
                        time.sleep(5.0)
                        continue
                else:
                    print(f"[Camera {self.camera_id}] Stream disconnected or frame read failed. Retrying...")
                    with self.lock:
                        self.is_online = False
                    cap.release()
                    cap = None
                    time.sleep(5.0)
                    continue

            # Pace local video files to simulate real-time camera feed
            if isinstance(self.source, str) and not self.source.startswith("rtsp"):
                fps = cap.get(cv2.CAP_PROP_FPS)
                if fps <= 0 or fps > 100:
                    fps = 15.0
                time.sleep(1.0 / fps)

            # Frame successfully read, update thread-safe variables
            with self.lock:
                self.latest_frame = frame
                self.frame_id += 1
                self.is_online = True

        if cap is not None:
            cap.release()
        print(f"[Camera {self.camera_id}] Capture thread stopped.")

    def get_latest_frame(self):
        with self.lock:
            # Return a copy to avoid multithreading modification issues, or return direct reference
            # For performance with OpenCV images, returning reference is okay as long as we treat it as read-only
            return self.latest_frame, self.frame_id, self.is_online

    def stop(self):
        self.stopped = True
        if self.thread is not None:
            self.thread.join(timeout=2.0)
