import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
