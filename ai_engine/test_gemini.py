import os
from dotenv import load_dotenv
from google import genai

# Load .env
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found.")
    exit()

print("API key found.")

# Create Gemini client
client = genai.Client(api_key=api_key)

# Send a simple test request
response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Say hello to DevPath AI in one sentence."
)

print("\nGemini response:")
print(response.text)