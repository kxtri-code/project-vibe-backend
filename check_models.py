from google import genai
import os

# --- PASTE YOUR KEY HERE ---
API_KEY = "AIzaSyBFtqVzgYZQBB7FAPSCVVPv6-ZIfs71Ogs"

client = genai.Client(api_key=API_KEY)

print("🔍 Scanning for available models...")
try:
    # We ask the API to list all models it has
    for model in client.models.list():
        # We only want models that can 'generateContent' (read images/text)
        if "generateContent" in model.supported_generation_methods:
            print(f"- {model.name}")
            
except Exception as e:
    print(f"❌ Error: {e}")