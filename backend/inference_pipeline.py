# backend/inference_pipeline.py
import cv2
import time
import os
import torch
from ultralytics import YOLO

class TwoStagePPEPipeline:
    def __init__(self, stage1_path='yolov11n.pt', stage2_path='models/ppe_crop_detector.pt', conf_threshold=0.50):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Initializing two-stage pipeline on device: {self.device}")
        
        # Load Stage 1: Person Detector (pretrained COCO)
        print(f"Loading Stage 1 Person Detector from: {stage1_path}")
        self.stage1_model = YOLO(stage1_path).to(self.device)
        
        # Load Stage 2: PPE Crop Detector
        # If user hasn't trained the custom model yet, fallback to stage1 model for architectural testing
        if os.path.exists(stage2_path):
            print(f"Loading Stage 2 PPE Crop Detector from: {stage2_path}")
            self.stage2_model = YOLO(stage2_path).to(self.device)
            self.fallback = False
        else:
            print(f"WARNING: Custom Stage 2 model '{stage2_path}' not found.")
            print(f"Falling back to pretrained Stage 1 model '{stage1_path}' for testing pipeline mechanics.")
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
                print(f"[Pipeline] Loaded thresholds from {config_path}: Person={self.person_conf_threshold}, PPE={self.ppe_conf_threshold}")
            except Exception as e:
                print(f"[Pipeline] Error loading config: {e}. Using defaults.")

        # Class names for Stage 2
        # Index: 0 -> helmet, 1 -> head (no helmet), 2 -> vest
        self.class_names = ['helmet', 'head', 'vest']
        
    def process_frame(self, frame):
        """
        Processes a single frame:
        1. Runs Stage 1 to detect persons.
        2. Crops each detected person.
        3. Runs Stage 2 on crops to detect helmet and vest.
        4. Applies compliance rules.
        5. Annotates the frame.
        """
        h_frame, w_frame = frame.shape[:2]
        
        # Stage 1: Person Detection
        # class 0 in COCO is 'person'
        s1_results = self.stage1_model.predict(
            source=frame,
            classes=[0], # Filter to only person class
            conf=self.person_conf_threshold,
            device=self.device,
            verbose=False
        )[0]
        
        annotated_frame = frame.copy()
        violations = []
        
        # Extract detected persons
        for idx, box in enumerate(s1_results.boxes):
            px1, py1, px2, py2 = map(int, box.xyxy[0].tolist())
            p_conf = float(box.conf[0])
            
            # Ensure boundaries are inside frame
            px1, py1 = max(0, px1), max(0, py1)
            px2, py2 = min(w_frame, px2), min(h_frame, py2)
            
            p_width = px2 - px1
            p_height = py2 - py1
            if p_width <= 0 or p_height <= 0: continue
            
            # Crop the person
            person_crop = frame[py1:py2, px1:px2]
            
            # Stage 2: PPE Detection on the crop
            # If using fallback model, mock the detection flags
            has_helmet = False
            has_head = False
            has_vest = False
            s2_conf = 0.0
            
            if not self.fallback:
                s2_results = self.stage2_model.predict(
                    source=person_crop,
                    conf=self.ppe_conf_threshold,
                    device=self.device,
                    verbose=False
                )[0]
                
                # Check detected classes inside the crop
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
                # Fallback mock logic for testing:
                # Let's mock compliance: alternate between compliant and non-compliant for demonstration
                has_helmet = (idx % 2 == 0)
                has_head = not has_helmet
                has_vest = (idx % 3 != 0)
                s2_conf = 0.85

            # Apply NTPC Safety Compliance Rules
            # Violations:
            # - Helmet missing: Has head (no helmet) or has no helmet at all
            # - Vest missing: Has no vest
            # - Compliant: Has helmet and has vest
            
            helmet_ok = has_helmet and not has_head
            vest_ok = has_vest
            
            if helmet_ok and vest_ok:
                status = "COMPLIANT"
                color = (0, 255, 0) # Green
            elif not helmet_ok and not vest_ok:
                status = "HELMET & VEST MISSING"
                color = (0, 0, 255) # Red
                violations.append({"type": "both_missing", "box": [px1, py1, px2, py2], "conf": s2_conf})
            elif not helmet_ok:
                status = "HELMET MISSING"
                color = (0, 165, 255) # Orange
                violations.append({"type": "helmet_missing", "box": [px1, py1, px2, py2], "conf": s2_conf})
            else:
                status = "VEST MISSING"
                color = (0, 255, 255) # Yellow
                violations.append({"type": "vest_missing", "box": [px1, py1, px2, py2], "conf": s2_conf})
                
            # Annotate the original frame
            cv2.rectangle(annotated_frame, (px1, py1), (px2, py2), color, 2)
            cv2.putText(
                annotated_frame,
                f"Worker {idx}: {status} (P_Conf: {p_conf:.2f})",
                (px1, py1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )
            
        return annotated_frame, violations

if __name__ == '__main__':
    # Test pipeline with a blank frame if executed directly
    pipeline = TwoStagePPEPipeline()
    dummy_frame = (np.random.rand(480, 640, 3) * 255).astype(np.uint8)
    out, viols = pipeline.process_frame(dummy_frame)
    print("Execution complete. Detections returned:", len(viols))
