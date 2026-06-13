# backend/test_integration.py
import unittest
import time
import os
import shutil
import numpy as np
import cv2
from datetime import datetime
from fastapi.testclient import TestClient

# Adjust path to find modules
import sys
sys.path.append(os.path.dirname(__file__))

from database import DatabaseManager
from storage import StorageManager
from app import app, db_manager, storage_manager

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Override database manager to force SQLite mode for testing
        db_manager.db_type = 'sqlite'
        db_manager._establish_connection()
        db_manager.init_db()
        
        # Override storage manager to force local fallback
        storage_manager.supabase = None
        
        cls.client = TestClient(app)

    def setUp(self):
        # Clean up tables before each test
        cursor, conn = db_manager.get_cursor()
        try:
            cursor.execute("DELETE FROM violations")
            cursor.execute("DELETE FROM cameras")
        finally:
            db_manager.release_cursor(cursor, conn)

    def test_camera_crud(self):
        # 1. Get initial cameras (should be empty because we cleaned them)
        response = self.client.get("/api/cameras")
        self.assertEqual(response.status_code, 200)
        cameras = response.json()
        self.assertEqual(len(cameras), 0)

        # 2. Add a camera
        camera_data = {
            "id": "test_cam",
            "rtsp_url": "backend/test_video_1.mp4",
            "zone_name": "Test Zone"
        }
        response = self.client.post("/api/cameras", json=camera_data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("upserted successfully", response.json()["message"])

        # 3. Verify camera was added
        response = self.client.get("/api/cameras")
        cameras = response.json()
        self.assertEqual(len(cameras), 1)
        self.assertEqual(cameras[0]["id"], "test_cam")
        self.assertEqual(cameras[0]["zone_name"], "Test Zone")

        # 4. Delete camera
        response = self.client.delete("/api/cameras/test_cam")
        self.assertEqual(response.status_code, 200)
        
        # 5. Verify camera was deleted
        response = self.client.get("/api/cameras")
        self.assertEqual(len(response.json()), 0)

    def test_violations_and_analytics(self):
        # 1. Insert mock cameras
        db_manager.upsert_camera("cam_1", "0", "Zone A")
        db_manager.upsert_camera("cam_2", "1", "Zone B")

        # 2. Save violations
        # Morning shift time (10:00 AM)
        t1 = datetime.now().replace(hour=10, minute=0, second=0)
        db_manager.save_violation("cam_1", "Zone A", t1, "helmet_missing", 0.85, "http://screenshot1.jpg", "morning")

        # Outside shift time (14:00 PM)
        t2 = datetime.now().replace(hour=14, minute=0, second=0)
        db_manager.save_violation("cam_2", "Zone B", t2, "vest_missing", 0.92, "http://screenshot2.jpg", "outside_shift")

        # 3. Verify violations query
        response = self.client.get("/api/violations")
        self.assertEqual(response.status_code, 200)
        violations = response.json()
        self.assertEqual(len(violations), 2)

        # 4. Test filtering by camera_id
        response = self.client.get("/api/violations?camera_id=cam_1")
        violations_filtered = response.json()
        self.assertEqual(len(violations_filtered), 1)
        self.assertEqual(violations_filtered[0]["camera_id"], "cam_1")
        self.assertEqual(violations_filtered[0]["violation_type"], "helmet_missing")

        # 5. Test filtering by shift
        response = self.client.get("/api/violations?shift=outside_shift")
        violations_filtered = response.json()
        self.assertEqual(len(violations_filtered), 1)
        self.assertEqual(violations_filtered[0]["camera_id"], "cam_2")

        # 6. Test analytics summary endpoint
        response = self.client.get("/api/analytics/summary")
        self.assertEqual(response.status_code, 200)
        summary = response.json()
        self.assertEqual(summary["total_violations"], 2)
        self.assertEqual(summary["type_counts"]["helmet_missing"], 1)
        self.assertEqual(summary["type_counts"]["vest_missing"], 1)
        self.assertEqual(summary["camera_counts"]["cam_1"], 1)
        self.assertEqual(summary["camera_counts"]["cam_2"], 1)
        self.assertEqual(summary["shift_counts"]["morning"], 1)
        self.assertEqual(summary["shift_counts"]["outside_shift"], 1)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

if __name__ == '__main__':
    unittest.main()
