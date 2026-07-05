import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SERVER_NAME = os.getenv("SERVER_NAME", "profile_lookup")
    URL_HOST_SERVER = os.getenv("URL_HOST_SERVER", "0.0.0.0")
    PORT_SERVER = int(os.getenv("PORT_SERVER", "8090"))
    RESOURCES_DIR = os.path.join(BASE_DIR, "..", "Resources")

    # --- RAG Engine (project riêng, gọi qua HTTP) ---
    RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8091")
    RAG_REQUEST_TIMEOUT_SECONDS = int(os.getenv("RAG_REQUEST_TIMEOUT_SECONDS", "30"))


config_object = Config()
