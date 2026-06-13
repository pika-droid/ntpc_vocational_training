# backend/shifts.py
import json
import os
from datetime import datetime, time

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "shifts_config.json")

def load_shifts(config_path=DEFAULT_CONFIG_PATH):
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Shifts] Error loading shifts config: {e}")
    # Default fallback
    return {
        "morning": {"start": "09:00", "end": "13:00"},
        "evening": {"start": "15:00", "end": "19:00"}
    }

def get_active_shift(timestamp, config_path=DEFAULT_CONFIG_PATH):
    """
    Determines which shift is active for a given timestamp.
    timestamp can be float (epoch time), str (iso format), or datetime object.
    Returns:
        str: Name of active shift (e.g. 'morning', 'evening', 'outside_shift')
    """
    if isinstance(timestamp, (float, int)):
        dt = datetime.fromtimestamp(timestamp)
    elif isinstance(timestamp, str):
        try:
            # Handle possible trailing Z or offsets
            normalized_str = timestamp.replace("Z", "")
            dt = datetime.fromisoformat(normalized_str)
        except ValueError:
            dt = datetime.now()
    elif isinstance(timestamp, datetime):
        dt = timestamp
    else:
        dt = datetime.now()
        
    t = dt.time()
    shifts = load_shifts(config_path)
    
    for shift_name, window in shifts.items():
        try:
            start_h, start_m = map(int, window["start"].split(":"))
            end_h, end_m = map(int, window["end"].split(":"))
            
            start_time = time(start_h, start_m)
            end_time = time(end_h, end_m)
            
            if start_time <= end_time:
                if start_time <= t <= end_time:
                    return shift_name
            else:
                # Overnight shift support (e.g. 22:00 to 06:00)
                if t >= start_time or t <= end_time:
                    return shift_name
        except Exception as e:
            print(f"[Shifts] Error parsing shift window for '{shift_name}': {e}")
            
    return "outside_shift"
