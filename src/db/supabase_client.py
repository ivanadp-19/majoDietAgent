from supabase import Client, create_client

from src.config import SUPABASE_PRIVATE_KEY, SUPABASE_URL

_client: Client | None = None


def get_supabase_client() -> Client:
    if SUPABASE_URL is None or SUPABASE_PRIVATE_KEY is None:
        raise ValueError("Missing Supabase credentials in environment")
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_PRIVATE_KEY)
    return _client
