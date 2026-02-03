import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PRIVATE_KEY = os.getenv("SUPABASE_PRIVATE_KEY")
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
