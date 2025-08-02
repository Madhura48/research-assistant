import os
from dotenv import load_dotenv

load_dotenv()

# Test environment variables
openai_key = os.getenv("OPENAI_API_KEY")
serper_key = os.getenv("SERPER_API_KEY")

print("="*50)
print("API KEY VERIFICATION")
print("="*50)
print("OpenAI API Key:", "✓ Set" if openai_key else "✗ Missing")
print("Serper API Key:", "✓ Set" if serper_key else "✗ Missing")
print("="*50)

if serper_key:
    print(f"Serper Key Preview: {serper_key[:10]}...")