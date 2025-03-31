import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")

# Converti stringa booleana in valore booleano
SKIP_INITIAL_CHARACTER_ANALYSIS = os.getenv("SKIP_INITIAL_CHARACTER_ANALYSIS", "false").lower() == "true"