import os
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: Gemini API key not found!")
else:
    print("Gemini API key loaded successfully!")
    print("Key length:", len(api_key))
    print("Key starts with:", api_key[:5])
    print("Key ends with:", api_key[-4:])