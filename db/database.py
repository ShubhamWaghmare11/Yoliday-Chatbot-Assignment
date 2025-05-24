from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv("PROJECT_URL"),os.getenv("PROJECT_KEY"))

