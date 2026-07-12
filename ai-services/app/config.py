import os
from dotenv import load_dotenv

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen-plus")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))

MAX_TOKENS = 2000
TEMPERATURE = 0.1