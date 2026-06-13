# backend/event_processor.py
import threading
import queue
import time
import cv2
import shifts

class EventProcessorWorker:
    def __init__(self, event_queue, db_manager, storage_manager):
        self.event_queue = event_queue
        self.db_manager = db_manager
        self.storage_manager = storage_manager
        
        self.stopped = False
        self.thread = None

    def start(self):
        self.stopped = False
        self.thread = threading.Thread(target=self._worker_loop, name="EventWorker", daemon=True)
        self.thread.start()
        print("[EventProcessor] Background worker thread started.")

    def stop(self):
        self.stopped = True
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        print("[EventProcessor] Background worker thread stopped.")

    def _worker_loop(self):
        while not self.stopped:
            try:
                # Retrieve event with timeout so we check self.stopped flag periodically
                event = self.event_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                # 1. Compress frame to JPEG bytes
                frame = event["frame"]
                success, encoded_img = cv2.imencode(".jpg", frame)
                if not success:
                    print(f"[EventProcessor] ERROR: Failed to encode frame to JPEG for Camera: {event['camera_id']}")
                    continue
                jpeg_bytes = encoded_img.tobytes()

                # 2. Upload screenshot to storage
                timestamp_sec = int(event["timestamp"])
                filename = f"violation_{event['camera_id']}_{timestamp_sec}.jpg"
                screenshot_url = self.storage_manager.upload_screenshot(filename, jpeg_bytes)

                # 3. Calculate active shift
                active_shift = shifts.get_active_shift(event["timestamp"])

                # 4. Save metadata to database
                self.db_manager.save_violation(
                    camera_id=event["camera_id"],
                    zone=event["zone"],
                    timestamp=event["timestamp"],
                    violation_type=event["violation_type"],
                    confidence=event["confidence"],
                    screenshot_url=screenshot_url,
                    shift=active_shift
                )
                print(f"[EventProcessor] Violation logged: Cam={event['camera_id']}, Zone={event['zone']}, Type={event['violation_type']}, Shift={active_shift}")
                
            except Exception as e:
                print(f"[EventProcessor] ERROR processing event: {e}")
            finally:
                self.event_queue.task_done()
