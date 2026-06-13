# backend/storage.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StorageManager:
    def __init__(self):
        self.supabase_url = os.environ.get("SUPABASE_URL")
        self.supabase_key = os.environ.get("SUPABASE_KEY")
        self.supabase = None
        
        # Local fallback directory
        self.local_dir = os.path.join(os.path.dirname(__file__), "static", "screenshots")
        os.makedirs(self.local_dir, exist_ok=True)
        print(f"[Storage] Local fallback directory: {self.local_dir}")
        
        if self.supabase_url and self.supabase_key:
            try:
                print(f"[Storage] Initializing Supabase client with URL: {self.supabase_url}")
                self.supabase = create_client(self.supabase_url, self.supabase_key)
                print("[Storage] Supabase client initialized successfully!")
            except Exception as e:
                print(f"[Storage] WARNING: Failed to initialize Supabase client: {e}")
                print("[Storage] Will default to local static files storage.")
        else:
            print("[Storage] Missing SUPABASE_URL or SUPABASE_KEY. Using local static files storage.")

    def upload_screenshot(self, filename, file_bytes):
        """
        Uploads file_bytes to Supabase object storage or local static files.
        Returns:
            str: Public URL to the uploaded screenshot.
        """
        # Save locally first as a backup and fallback
        local_path = os.path.join(self.local_dir, filename)
        try:
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            # Local URL format
            local_url = f"/static/screenshots/{filename}"
        except Exception as e:
            print(f"[Storage] Error saving local backup screenshot: {e}")
            local_url = None

        # Try uploading to Supabase if client is available
        if self.supabase:
            try:
                # Upload bytes directly
                bucket = "violations"
                # Use folder-like hierarchy in Supabase if needed (e.g. 'screenshots/filename')
                # If the folder doesn't exist it is created automatically
                path = f"screenshots/{filename}"
                
                # Check if bucket exists/is accessible by trying upload
                # Content type image/jpeg is specified in headers
                res = self.supabase.storage.from_(bucket).upload(
                    path=path,
                    file=file_bytes,
                    file_options={"content-type": "image/jpeg", "upsert": "true"}
                )
                
                # Retrieve public URL
                public_url = self.supabase.storage.from_(bucket).get_public_url(path)
                print(f"[Storage] Uploaded screenshot to Supabase Storage: {public_url}")
                return public_url
            except Exception as e:
                print(f"[Storage] WARNING: Supabase upload failed: {e}. Falling back to local URL.")
                
        return local_url
