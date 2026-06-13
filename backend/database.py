# backend/database.py
import os
import time
import sqlite3
from datetime import datetime
import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.db_type = None  # 'postgresql' or 'sqlite'
        self.sqlite_conn = None
        self.pg_pool = None
        
        # Check database variables
        self.db_url = os.environ.get("DATABASE_URL")
        self.db_host = os.environ.get("DB_HOST")
        self.db_port = os.environ.get("DB_PORT", "5432")
        self.db_name = os.environ.get("DB_NAME")
        self.db_user = os.environ.get("DB_USER")
        self.db_pass = os.environ.get("DB_PASSWORD")
        
        self._establish_connection()

    def _establish_connection(self):
        # Check if PostgreSQL connection variables are available
        has_pg_creds = self.db_url or (self.db_host and self.db_name and self.db_user and self.db_pass)
        
        if has_pg_creds:
            try:
                print("[Database] Attempting to connect to PostgreSQL...")
                if self.db_url:
                    self.pg_pool = psycopg2.pool.SimpleConnectionPool(1, 5, dsn=self.db_url)
                else:
                    self.pg_pool = psycopg2.pool.SimpleConnectionPool(
                        1, 5,
                        host=self.db_host,
                        port=self.db_port,
                        database=self.db_name,
                        user=self.db_user,
                        password=self.db_pass
                    )
                self.db_type = 'postgresql'
                print("[Database] PostgreSQL connection pool initialized successfully!")
                return
            except Exception as e:
                print(f"[Database] WARNING: PostgreSQL connection failed: {e}")
                print("[Database] Falling back to SQLite.")
        else:
            print("[Database] No PostgreSQL credentials found in environment. Using SQLite.")
            
        # SQLite Fallback
        self.db_type = 'sqlite'
        db_path = os.path.join(os.path.dirname(__file__), "violations.db")
        print(f"[Database] SQLite file: {db_path}")
        self.sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.sqlite_conn.row_factory = sqlite3.Row

    def get_cursor(self):
        """Returns a cursor and connection/pool reference for transaction context."""
        if self.db_type == 'postgresql':
            conn = self.pg_pool.getconn()
            # Set autocommit to True for simple CRUD/upserts or manage it in wrapper
            conn.autocommit = True
            return conn.cursor(), conn
        else:
            # For SQLite, we share the single connection
            return self.sqlite_conn.cursor(), self.sqlite_conn

    def release_cursor(self, cursor, conn):
        """Closes cursor and releases pg connection back to pool."""
        if cursor:
            cursor.close()
        if self.db_type == 'postgresql' and conn:
            self.pg_pool.putconn(conn)
        elif self.db_type == 'sqlite' and conn:
            conn.commit()

    def init_db(self):
        """Creates tables if they do not exist."""
        cursor, conn = self.get_cursor()
        try:
            if self.db_type == 'postgresql':
                # PostgreSQL schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cameras (
                        id VARCHAR(50) PRIMARY KEY,
                        rtsp_url VARCHAR(255) NOT NULL,
                        zone_name VARCHAR(100) NOT NULL,
                        is_online BOOLEAN DEFAULT FALSE,
                        last_seen TIMESTAMP WITH TIME ZONE
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS violations (
                        id SERIAL PRIMARY KEY,
                        camera_id VARCHAR(50) REFERENCES cameras(id) ON DELETE SET NULL,
                        zone VARCHAR(100) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                        violation_type VARCHAR(50) NOT NULL,
                        confidence FLOAT NOT NULL,
                        screenshot_url VARCHAR(500),
                        shift VARCHAR(50) NOT NULL
                    );
                """)
            else:
                # SQLite schema
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cameras (
                        id TEXT PRIMARY KEY,
                        rtsp_url TEXT NOT NULL,
                        zone_name TEXT NOT NULL,
                        is_online BOOLEAN DEFAULT 0,
                        last_seen TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS violations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        camera_id TEXT,
                        zone TEXT NOT NULL,
                        timestamp TIMESTAMP NOT NULL,
                        violation_type TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        screenshot_url TEXT,
                        shift TEXT NOT NULL,
                        FOREIGN KEY (camera_id) REFERENCES cameras (id) ON DELETE SET NULL
                    );
                """)
            print(f"[Database] Schema initialized successfully on '{self.db_type}'.")
        except Exception as e:
            print(f"[Database] Error initializing database schema: {e}")
            raise e
        finally:
            self.release_cursor(cursor, conn)

    # Camera CRUD Methods
    def get_cameras(self):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute("SELECT id, rtsp_url, zone_name, is_online, last_seen FROM cameras")
            rows = cursor.fetchall()
            cameras = []
            for row in rows:
                cameras.append({
                    "id": row[0] if self.db_type == 'postgresql' else row['id'],
                    "rtsp_url": row[1] if self.db_type == 'postgresql' else row['rtsp_url'],
                    "zone_name": row[2] if self.db_type == 'postgresql' else row['zone_name'],
                    "is_online": bool(row[3]) if self.db_type == 'postgresql' else bool(row['is_online']),
                    "last_seen": row[4] if self.db_type == 'postgresql' else row['last_seen']
                })
            return cameras
        finally:
            self.release_cursor(cursor, conn)

    def get_camera(self, camera_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute("SELECT id, rtsp_url, zone_name, is_online, last_seen FROM cameras WHERE id = %s" if self.db_type == 'postgresql' else "SELECT id, rtsp_url, zone_name, is_online, last_seen FROM cameras WHERE id = ?", (camera_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0] if self.db_type == 'postgresql' else row['id'],
                    "rtsp_url": row[1] if self.db_type == 'postgresql' else row['rtsp_url'],
                    "zone_name": row[2] if self.db_type == 'postgresql' else row['zone_name'],
                    "is_online": bool(row[3]) if self.db_type == 'postgresql' else bool(row['is_online']),
                    "last_seen": row[4] if self.db_type == 'postgresql' else row['last_seen']
                }
            return None
        finally:
            self.release_cursor(cursor, conn)

    def upsert_camera(self, camera_id, rtsp_url, zone_name, is_online=False):
        cursor, conn = self.get_cursor()
        now = datetime.now()
        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO cameras (id, rtsp_url, zone_name, is_online, last_seen)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) 
                    DO UPDATE SET rtsp_url = EXCLUDED.rtsp_url, 
                                  zone_name = EXCLUDED.zone_name,
                                  is_online = EXCLUDED.is_online,
                                  last_seen = EXCLUDED.last_seen
                """, (camera_id, rtsp_url, zone_name, is_online, now))
            else:
                cursor.execute("""
                    INSERT INTO cameras (id, rtsp_url, zone_name, is_online, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) 
                    DO UPDATE SET rtsp_url = excluded.rtsp_url, 
                                  zone_name = excluded.zone_name,
                                  is_online = excluded.is_online,
                                  last_seen = excluded.last_seen
                """, (camera_id, rtsp_url, zone_name, int(is_online), now.isoformat()))
        finally:
            self.release_cursor(cursor, conn)

    def delete_camera(self, camera_id):
        cursor, conn = self.get_cursor()
        try:
            cursor.execute("DELETE FROM cameras WHERE id = %s" if self.db_type == 'postgresql' else "DELETE FROM cameras WHERE id = ?", (camera_id,))
        finally:
            self.release_cursor(cursor, conn)

    def update_camera_status(self, camera_id, is_online):
        cursor, conn = self.get_cursor()
        now = datetime.now()
        try:
            if self.db_type == 'postgresql':
                cursor.execute("""
                    UPDATE cameras 
                    SET is_online = %s, last_seen = %s 
                    WHERE id = %s
                """, (is_online, now, camera_id))
            else:
                cursor.execute("""
                    UPDATE cameras 
                    SET is_online = ?, last_seen = ? 
                    WHERE id = ?
                """, (int(is_online), now.isoformat(), camera_id))
        finally:
            self.release_cursor(cursor, conn)

    # Violation CRUD Methods
    def save_violation(self, camera_id, zone, timestamp, violation_type, confidence, screenshot_url, shift):
        cursor, conn = self.get_cursor()
        try:
            # Ensure timestamp is datetime
            if isinstance(timestamp, float) or isinstance(timestamp, int):
                dt = datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp)
                except ValueError:
                    dt = datetime.now()
            else:
                dt = timestamp

            if self.db_type == 'postgresql':
                cursor.execute("""
                    INSERT INTO violations (camera_id, zone, timestamp, violation_type, confidence, screenshot_url, shift)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (camera_id, zone, dt, violation_type, confidence, screenshot_url, shift))
            else:
                cursor.execute("""
                    INSERT INTO violations (camera_id, zone, timestamp, violation_type, confidence, screenshot_url, shift)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (camera_id, zone, dt.isoformat(), violation_type, confidence, screenshot_url, shift))
        finally:
            self.release_cursor(cursor, conn)

    def get_violations(self, camera_id=None, zone=None, violation_type=None, shift=None, start_date=None, end_date=None):
        cursor, conn = self.get_cursor()
        try:
            query = "SELECT id, camera_id, zone, timestamp, violation_type, confidence, screenshot_url, shift FROM violations WHERE 1=1"
            params = []
            
            if camera_id:
                query += " AND camera_id = %s" if self.db_type == 'postgresql' else " AND camera_id = ?"
                params.append(camera_id)
            if zone:
                query += " AND zone = %s" if self.db_type == 'postgresql' else " AND zone = ?"
                params.append(zone)
            if violation_type:
                query += " AND violation_type = %s" if self.db_type == 'postgresql' else " AND violation_type = ?"
                params.append(violation_type)
            if shift:
                query += " AND shift = %s" if self.db_type == 'postgresql' else " AND shift = ?"
                params.append(shift)
            if start_date:
                query += " AND timestamp >= %s" if self.db_type == 'postgresql' else " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= %s" if self.db_type == 'postgresql' else " AND timestamp <= ?"
                params.append(end_date)
                
            query += " ORDER BY timestamp DESC"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            violations = []
            for row in rows:
                violations.append({
                    "id": row[0] if self.db_type == 'postgresql' else row['id'],
                    "camera_id": row[1] if self.db_type == 'postgresql' else row['camera_id'],
                    "zone": row[2] if self.db_type == 'postgresql' else row['zone'],
                    "timestamp": row[3] if self.db_type == 'postgresql' else row['timestamp'],
                    "violation_type": row[4] if self.db_type == 'postgresql' else row['violation_type'],
                    "confidence": float(row[5]) if self.db_type == 'postgresql' else float(row['confidence']),
                    "screenshot_url": row[6] if self.db_type == 'postgresql' else row['screenshot_url'],
                    "shift": row[7] if self.db_type == 'postgresql' else row['shift']
                })
            return violations
        finally:
            self.release_cursor(cursor, conn)

    def get_analytics_summary(self):
        cursor, conn = self.get_cursor()
        try:
            # We can run distinct aggregate queries to populate dashboards
            # 1. Total violations
            cursor.execute("SELECT COUNT(*) FROM violations")
            total_violations = cursor.fetchone()[0]
            
            # 2. Helmet vs Vest counts
            cursor.execute("SELECT violation_type, COUNT(*) FROM violations GROUP BY violation_type")
            type_counts = {r[0]: r[1] for r in cursor.fetchall()}
            
            # 3. Counts by camera
            cursor.execute("SELECT camera_id, COUNT(*) FROM violations GROUP BY camera_id")
            camera_counts = {r[0]: r[1] for r in cursor.fetchall()}
            
            # 4. Counts by zone
            cursor.execute("SELECT zone, COUNT(*) FROM violations GROUP BY zone")
            zone_counts = {r[0]: r[1] for r in cursor.fetchall()}
            
            # 5. Counts by shift
            cursor.execute("SELECT shift, COUNT(*) FROM violations GROUP BY shift")
            shift_counts = {r[0]: r[1] for r in cursor.fetchall()}
            
            # 6. Hourly distribution
            if self.db_type == 'postgresql':
                cursor.execute("SELECT EXTRACT(HOUR FROM timestamp) as hr, COUNT(*) FROM violations GROUP BY hr ORDER BY hr")
            else:
                cursor.execute("SELECT strftime('%H', timestamp) as hr, COUNT(*) FROM violations GROUP BY hr ORDER BY hr")
            hourly_counts = {int(r[0]): r[1] for r in cursor.fetchall() if r[0] is not None}
            
            return {
                "total_violations": total_violations,
                "type_counts": type_counts,
                "camera_counts": camera_counts,
                "zone_counts": zone_counts,
                "shift_counts": shift_counts,
                "hourly_counts": hourly_counts
            }
        finally:
            self.release_cursor(cursor, conn)
