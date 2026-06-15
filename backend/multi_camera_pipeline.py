# backend/multi_camera_pipeline.py
import time
import os
import cv2
import threading
import queue
from ultralytics import YOLO
import torch
from camera_capture import CameraCapture
from violation_rules import ViolationStateMachine

class MultiCameraPPEPipeline:
    def __init__(self, camera_configs, stage1_path='yolov11n.pt', stage2_path='models/ppe_crop_detector.pt', conf_threshold=0.50):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"[MultiCameraPipeline] Running on device: {self.device}")
        
        self.stage1_path = stage1_path
        self.stage2_path = stage2_path
        
        # Load Stage 2 model (stateless)
        if os.path.exists(stage2_path):
            print(f"[MultiCameraPipeline] Loading Stage 2 model: {stage2_path}")
            self.stage2_model = YOLO(stage2_path).to(self.device)
            self.fallback = False
        else:
            print(f"[MultiCameraPipeline] WARNING: Custom Stage 2 model '{stage2_path}' not found.")
            print(f"[MultiCameraPipeline] Falling back to pretrained Stage 1 model '{stage1_path}' for testing pipeline.")
            self.stage2_model = YOLO(stage1_path).to(self.device)
            self.fallback = True
        self.conf_threshold = conf_threshold
        # Load config thresholds
        config_path = os.path.join(os.path.dirname(__file__), 'inference_config.json')
        self.person_conf_threshold = conf_threshold
        self.ppe_conf_threshold = conf_threshold
        if os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)
                self.person_conf_threshold = config.get("person_conf_threshold", conf_threshold)
                self.ppe_conf_threshold = config.get("ppe_conf_threshold", conf_threshold)
                print(f"[MultiCameraPipeline] Loaded thresholds: Person={self.person_conf_threshold}, PPE={self.ppe_conf_threshold}")
            except Exception as e:
                print(f"[MultiCameraPipeline] Error loading config: {e}. Using defaults.")

        self.camera_configs = {}
        
        self.lock = threading.Lock()
        self.event_queue = queue.Queue()
        
        # Instantiate separate Stage 1 YOLO models for tracking per camera
        self.stage1_models = {}
        # Threaded captures
        self.captures = {}
        self.last_processed_ids = {}
        self.latest_processed_frames = {}
        
        # Initialize starting cameras
        for cam_id, config in camera_configs.items():
            self.add_camera(cam_id, config.get('rtsp_url'), config.get('zone_name', 'default_zone'))
            
        # State machine
        self.vsm = ViolationStateMachine()
        
        # Event logging
        self.confirmed_violations = []
        
        # Loop control
        self.stopped = False
        self.loop_thread = None
        self.track_history = {}

    def add_camera(self, cam_id, rtsp_url, zone_name):
        with self.lock:
            if cam_id in self.camera_configs:
                print(f"[MultiCameraPipeline] Camera '{cam_id}' already exists. Updating configuration...")
                # Stop existing camera first
                cap = self.captures.get(cam_id)
                if cap:
                    cap.stop()
            
            print(f"[MultiCameraPipeline] Adding camera '{cam_id}' (Zone: {zone_name}, Source: {rtsp_url})")
            self.camera_configs[cam_id] = {
                "rtsp_url": rtsp_url,
                "zone_name": zone_name
            }
            self.captures[cam_id] = CameraCapture(cam_id, rtsp_url, zone_name)
            self.stage1_models[cam_id] = YOLO(self.stage1_path).to(self.device)
            self.last_processed_ids[cam_id] = -1
            self.latest_processed_frames[cam_id] = None

    def remove_camera(self, cam_id):
        with self.lock:
            if cam_id not in self.camera_configs:
                print(f"[MultiCameraPipeline] Camera '{cam_id}' not found for removal.")
                return
                
            print(f"[MultiCameraPipeline] Removing camera '{cam_id}'")
            cap = self.captures.pop(cam_id, None)
            if cap:
                cap.stop()
                
            self.camera_configs.pop(cam_id, None)
            self.stage1_models.pop(cam_id, None)
            self.last_processed_ids.pop(cam_id, None)
            self.latest_processed_frames.pop(cam_id, None)

    def start(self):
        self.stopped = False
        self.loop_thread = threading.Thread(target=self._processing_loop, name="InferenceLoop", daemon=True)
        self.loop_thread.start()
        
    def stop(self):
        self.stopped = True
        if self.loop_thread is not None:
            self.loop_thread.join(timeout=2.0)
        with self.lock:
            for cap in self.captures.values():
                cap.stop()

    def _processing_loop(self):
        print("[MultiCameraPipeline] Inference loop started.")
        while not self.stopped:
            processed_any = False
            current_time = time.time()
            
            with self.lock:
                active_cam_ids = list(self.camera_configs.keys())
                
            for cam_id in active_cam_ids:
                with self.lock:
                    cap = self.captures.get(cam_id)
                
                if cap is None:
                    continue
                    
                frame, frame_id, is_online = cap.get_latest_frame()
                
                # Only process if camera is online, frame exists, and it is a new frame
                if is_online and frame is not None and frame_id > self.last_processed_ids.get(cam_id, -1):
                    # Process frame
                    annotated_frame = self.process_frame(cam_id, frame, current_time)
                    with self.lock:
                        self.latest_processed_frames[cam_id] = annotated_frame
                        self.last_processed_ids[cam_id] = frame_id
                    processed_any = True
                    
                    # Cleanup old tracks for this camera
                    self.vsm.cleanup_tracks(cam_id, current_time)
                    
                    # Sync track_history with state machine active tracks
                    if cam_id in self.track_history and cam_id in self.vsm.track_states:
                        active_tracks = set(self.vsm.track_states[cam_id].keys())
                        for tid in list(self.track_history[cam_id].keys()):
                            if tid not in active_tracks:
                                del self.track_history[cam_id][tid]
                    
            if not processed_any:
                time.sleep(0.005) # Yield CPU if no new frames are ready
                
        print("[MultiCameraPipeline] Inference loop stopped.")

    def process_frame(self, cam_id, frame, current_time):
        h_frame, w_frame = frame.shape[:2]
        
        # Run Stage 1 with tracking: classes=[0] for person
        s1_results = self.stage1_models[cam_id].track(
            source=frame,
            classes=[0],
            conf=self.person_conf_threshold,
            device=self.device,
            verbose=False,
            persist=True
        )[0]
        
        annotated_frame = frame.copy()
        
        if s1_results.boxes is None or len(s1_results.boxes) == 0:
            return annotated_frame
            
        # Extract detected persons
        for idx, box in enumerate(s1_results.boxes):
            px1, py1, px2, py2 = map(int, box.xyxy[0].tolist())
            p_conf = float(box.conf[0])
            
            # If tracking ID is not assigned yet (e.g. first frame), fallback to index
            track_id = int(box.id[0]) if box.id is not None else -(idx + 1)
            
            # Ensure boundaries are inside frame
            px1, py1 = max(0, px1), max(0, py1)
            px2, py2 = min(w_frame, px2), min(h_frame, py2)
            
            p_width = px2 - px1
            p_height = py2 - py1
            if p_width <= 0 or p_height <= 0: continue
            
            # Apply padding margin (10% width, 15% height) to avoid clipping helmets/vests
            pad_w = int(p_width * 0.10)
            pad_h = int(p_height * 0.15)
            
            pad_x1 = max(0, px1 - pad_w)
            pad_y1 = max(0, py1 - pad_h)
            pad_x2 = min(w_frame, px2 + pad_w)
            pad_y2 = min(h_frame, py2 + pad_h)
            
            if (pad_x2 - pad_x1) <= 0 or (pad_y2 - pad_y1) <= 0: continue
            
            # Crop the person with padding
            person_crop = frame[pad_y1:pad_y2, pad_x1:pad_x2]
            
            has_helmet = False
            has_head = False
            has_vest = False
            s2_conf = 0.0
            
            if not self.fallback:
                # Stage 2: PPE Detection on crop
                s2_results = self.stage2_model.predict(
                    source=person_crop,
                    conf=self.ppe_conf_threshold,
                    device=self.device,
                    verbose=False
                )[0]
                
                for s2_box in s2_results.boxes:
                    cid = int(s2_box.cls[0])
                    s2_conf = max(s2_conf, float(s2_box.conf[0]))
                    
                    if cid == 0: # helmet
                        has_helmet = True
                    elif cid == 1: # head (unprotected head)
                        has_head = True
                    elif cid == 2: # vest
                        has_vest = True
            else:
                # Fallback mock logic for testing pipeline mechanics
                # Alternate safety compliance states based on track ID
                has_helmet = (track_id % 2 == 0)
                has_head = not has_helmet
                has_vest = (track_id % 3 != 0)
                s2_conf = 0.85
                
            helmet_ok = has_helmet and not has_head
            vest_ok = has_vest
            is_compliant = helmet_ok and vest_ok
            
            violation_type = None
            if not is_compliant:
                if not helmet_ok and not vest_ok:
                    violation_type = "both_missing"
                elif not helmet_ok:
                    violation_type = "helmet_missing"
                else:
                    violation_type = "vest_missing"
                    
            # Temporal Smoothing (majority voting over a 5-frame window)
            if cam_id not in self.track_history:
                self.track_history[cam_id] = {}
            if track_id not in self.track_history[cam_id]:
                self.track_history[cam_id][track_id] = []
                
            self.track_history[cam_id][track_id].append((is_compliant, violation_type))
            if len(self.track_history[cam_id][track_id]) > 5:
                self.track_history[cam_id][track_id].pop(0)
                
            history = self.track_history[cam_id][track_id]
            non_compliant_frames = [h for h in history if not h[0]]
            is_compliant_smoothed = len(non_compliant_frames) <= (len(history) / 2.0)
            
            violation_type_smoothed = None
            if not is_compliant_smoothed:
                from collections import Counter
                types = [h[1] for h in history if h[1] is not None]
                violation_type_smoothed = Counter(types).most_common(1)[0][0] if types else violation_type
                
                if violation_type_smoothed == "both_missing":
                    status = "HELMET & VEST MISSING"
                    color = (0, 0, 255) # Red
                elif violation_type_smoothed == "helmet_missing":
                    status = "HELMET MISSING"
                    color = (0, 165, 255) # Orange
                else:
                    status = "VEST MISSING"
                    color = (0, 255, 255) # Yellow
            else:
                status = "COMPLIANT"
                color = (0, 255, 0) # Green
                
            # Update compliance state machine for this track with smoothed results
            violation_event = self.vsm.update_track(cam_id, track_id, is_compliant_smoothed, violation_type_smoothed, current_time)
            
            if violation_event is not None:
                # Attach additional details like crop boundary and conf
                violation_event["box"] = [px1, py1, px2, py2]
                violation_event["conf"] = s2_conf
                self.confirmed_violations.append(violation_event)
                
                with self.lock:
                    zone_name = self.camera_configs[cam_id].get("zone_name", "unknown") if cam_id in self.camera_configs else "unknown"
                
                # Push to background event queue
                event = {
                    "camera_id": cam_id,
                    "zone": zone_name,
                    "timestamp": current_time,
                    "violation_type": violation_type,
                    "confidence": float(s2_conf),
                    "frame": annotated_frame.copy()
                }
                self.event_queue.put(event)
                
                print(f"\n[ALERT] Confirmed Violation on Cam '{cam_id}' (Zone: {zone_name})! "
                      f"Track {track_id} is {status}. Confidence: {s2_conf:.2f}")

            # Annotate the original frame
            cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), color, 2)
            cv2.putText(
                annotated_frame,
                f"Worker {track_id}: {status} (P: {p_conf:.2f})",
                (px1, py1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )
            
        return annotated_frame
