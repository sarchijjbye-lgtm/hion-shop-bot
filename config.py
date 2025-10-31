import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))  # можно не указывать
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "HION Orders")
