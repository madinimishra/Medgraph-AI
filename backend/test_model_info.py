from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for m in client.models.list():
    if "gemini-2.5-flash" in m.name:
        print("=" * 50)
        print("Name:", m.name)
        print("Display Name:", getattr(m, "display_name", None))
        print("Supported Methods:", getattr(m, "supported_actions", None))
        print(m)