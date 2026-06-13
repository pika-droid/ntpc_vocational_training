# backend/test_state_machine.py
import unittest
import time
import os
import json
from violation_rules import ViolationStateMachine

class TestViolationStateMachine(unittest.TestCase):
    def setUp(self):
        # Write a temporary test config to avoid reading/writing the main config
        self.test_config_path = "backend/test_rules_config.json"
        self.config_data = {
            "violation_window_seconds": 2.0,
            "track_loss_timeout_seconds": 1.0,
            "alert_cooldown_seconds": 30.0
        }
        with open(self.test_config_path, 'w') as f:
            json.dump(self.config_data, f)
            
        self.vsm = ViolationStateMachine(config_path=self.test_config_path)

    def tearDown(self):
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    def test_happy_path(self):
        # Worker remains compliant -> No violation
        t = 100.0
        res = self.vsm.update_track(camera_id="cam_1", track_id=1, is_compliant=True, violation_type=None, current_time=t)
        self.assertIsNone(res)
        
        t += 1.0
        res = self.vsm.update_track(camera_id="cam_1", track_id=1, is_compliant=True, violation_type=None, current_time=t)
        self.assertIsNone(res)

    def test_brief_violation(self):
        # Worker is non-compliant for 1.5s, then becomes compliant -> No violation triggered
        t = 100.0
        # First non-compliant frame
        res = self.vsm.update_track("cam_1", 1, is_compliant=False, violation_type="helmet_missing", current_time=t)
        self.assertIsNone(res)
        
        # 1.5 seconds later, still non-compliant
        t += 1.5
        res = self.vsm.update_track("cam_1", 1, is_compliant=False, violation_type="helmet_missing", current_time=t)
        self.assertIsNone(res)
        
        # 1.6 seconds later, becomes compliant
        t += 0.1
        res = self.vsm.update_track("cam_1", 1, is_compliant=True, violation_type=None, current_time=t)
        self.assertIsNone(res)
        
        # 2.5 seconds from start (total non-compliant duration was interrupted) -> No violation
        t += 0.9
        res = self.vsm.update_track("cam_1", 1, is_compliant=False, violation_type="helmet_missing", current_time=t)
        self.assertIsNone(res)

    def test_confirmed_violation(self):
        # Worker is non-compliant for 2.1s -> Violation triggers
        t = 100.0
        res = self.vsm.update_track("cam_1", 1, is_compliant=False, violation_type="helmet_missing", current_time=t)
        self.assertIsNone(res)
        
        t += 1.0
        res = self.vsm.update_track("cam_1", 1, is_compliant=False, violation_type="helmet_missing", current_time=t)
        self.assertIsNone(res)
        
        t += 1.1 # Total elapsed: 2.1s (>= 2.0s)
        res = self.vsm.update_track("cam_1", 1, is_compliant=False, violation_type="helmet_missing", current_time=t)
        
        self.assertIsNotNone(res)
        self.assertEqual(res["camera_id"], "cam_1")
        self.assertEqual(res["track_id"], 1)
        self.assertEqual(res["violation_type"], "helmet_missing")
        self.assertEqual(res["duration"], 2.1)

    def test_cooldown(self):
        # Worker is non-compliant for 10s after violation -> Only 1 violation is triggered
        t = 100.0
        # Trigger violation
        self.vsm.update_track("cam_1", 1, False, "vest_missing", t)
        t += 1.0
        self.vsm.update_track("cam_1", 1, False, "vest_missing", t)
        t += 1.1
        res = self.vsm.update_track("cam_1", 1, False, "vest_missing", t)
        self.assertIsNotNone(res) # Violation triggered
        
        # Subsequent updates during cooldown should return None
        for _ in range(5):
            t += 1.0
            res = self.vsm.update_track("cam_1", 1, False, "vest_missing", t)
            self.assertIsNone(res)

    def test_cooldown_expiry(self):
        # Worker is non-compliant for 35s after violation -> A second violation is triggered
        t = 100.0
        # Trigger first violation
        self.vsm.update_track("cam_1", 1, False, "both_missing", t)
        t += 2.0
        res = self.vsm.update_track("cam_1", 1, False, "both_missing", t)
        self.assertIsNotNone(res)
        
        # Wait 31 seconds (past 30s cooldown)
        t += 31.0
        res = self.vsm.update_track("cam_1", 1, False, "both_missing", t)
        self.assertIsNotNone(res) # Second violation triggered
        self.assertEqual(res["track_id"], 1)

    def test_track_loss(self):
        # Worker is non-compliant for 1s, goes missing for 1.5s (>1s timeout), then returns non-compliant
        # -> Timer resets on missing and starts from 0 upon return
        t = 100.0
        self.vsm.update_track("cam_1", 1, False, "helmet_missing", t)
        
        t += 1.0
        self.vsm.update_track("cam_1", 1, False, "helmet_missing", t)
        
        # Cleanup tracks at t=102.5. Track 1 last seen at 101.0, so difference is 1.5s (> 1.0s timeout)
        t += 1.5
        self.vsm.cleanup_tracks("cam_1", current_time=t)
        self.assertNotIn(1, self.vsm.track_states["cam_1"]) # Track should be removed
        
        # Worker reappears as non-compliant
        res = self.vsm.update_track("cam_1", 1, False, "helmet_missing", current_time=t)
        self.assertIsNone(res) # No immediate violation since track state was reset
        
        t += 1.0
        res = self.vsm.update_track("cam_1", 1, False, "helmet_missing", current_time=t)
        self.assertIsNone(res)
        
        t += 1.1 # 2.1s after reappearance -> Violation triggers
        res = self.vsm.update_track("cam_1", 1, False, "helmet_missing", current_time=t)
        self.assertIsNotNone(res)

if __name__ == '__main__':
    unittest.main()
