# backend/violation_rules.py
import json
import os
import time

DEFAULT_CONFIG_PATH = "backend/violation_rules_config.json"
DEFAULT_CONFIG = {
    "violation_window_seconds": 2.0,
    "track_loss_timeout_seconds": 1.0,
    "alert_cooldown_seconds": 30.0
}

class ViolationStateMachine:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config = self.load_config()
        
        # track_states[camera_id][track_id] = {
        #     'first_non_compliant_time': None / float,
        #     'last_seen_time': float,
        #     'alert_triggered': bool,
        #     'alert_time': float,
        #     'violation_type': str
        # }
        self.track_states = {}

    def load_config(self):
        """Loads configuration from JSON file or creates a default one if missing."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                print(f"[Rules Engine] Loaded config from {self.config_path}: {config}")
                return config
            except Exception as e:
                print(f"[Rules Engine] Error loading config: {e}. Using defaults.")
        
        # Create default config file if it does not exist
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            print(f"[Rules Engine] Created default config at {self.config_path}")
        except Exception as e:
            print(f"[Rules Engine] Failed to write default config: {e}")
            
        return DEFAULT_CONFIG.copy()

    def update_track(self, camera_id, track_id, is_compliant, violation_type, current_time=None):
        """
        Updates the compliance state of a track.
        Returns:
            dict or None: A violation event dictionary if a new alert is triggered, otherwise None.
        """
        if current_time is None:
            current_time = time.time()

        if camera_id not in self.track_states:
            self.track_states[camera_id] = {}

        # Initialize track state if new
        if track_id not in self.track_states[camera_id]:
            self.track_states[camera_id][track_id] = {
                'first_non_compliant_time': None,
                'last_seen_time': current_time,
                'alert_triggered': False,
                'alert_time': 0.0,
                'violation_type': None
            }

        state = self.track_states[camera_id][track_id]
        state['last_seen_time'] = current_time

        # If compliant, reset non-compliance timer
        if is_compliant:
            state['first_non_compliant_time'] = None
            state['violation_type'] = None
            return None

        # If non-compliant:
        state['violation_type'] = violation_type

        # Start timer if not already running
        if state['first_non_compliant_time'] is None:
            state['first_non_compliant_time'] = current_time
            return None

        # Check if non-compliance has persisted past the threshold window
        elapsed = current_time - state['first_non_compliant_time']
        window = self.config.get("violation_window_seconds", 2.0)
        
        if elapsed >= window:
            cooldown = self.config.get("alert_cooldown_seconds", 30.0)
            should_alert = not state['alert_triggered'] or (current_time - state['alert_time'] >= cooldown)
            if should_alert:
                state['alert_triggered'] = True
                state['alert_time'] = current_time
                
                # Return violation event details
                return {
                    "camera_id": camera_id,
                    "track_id": track_id,
                    "violation_type": violation_type,
                    "timestamp": current_time,
                    "duration": round(elapsed, 2)
                }
                
        return None

    def cleanup_tracks(self, camera_id, current_time=None):
        """Removes tracks that haven't been seen within the track_loss_timeout window."""
        if current_time is None:
            current_time = time.time()

        if camera_id not in self.track_states:
            return

        timeout = self.config.get("track_loss_timeout_seconds", 1.0)
        tracks_to_delete = []
        
        for track_id, state in self.track_states[camera_id].items():
            if current_time - state['last_seen_time'] > timeout:
                tracks_to_delete.append(track_id)

        for track_id in tracks_to_delete:
            del self.track_states[camera_id][track_id]
            print(f"[Rules Engine] Track {track_id} on Camera {camera_id} cleared due to track loss timeout.")
