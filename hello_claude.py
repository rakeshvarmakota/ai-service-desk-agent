"""Quick test: checks that the Claude API key works."""

import os

from anthropic import Anthropic
from dotenv import load_dotenv

# Load ANTHROPIC_API_KEY (and optional CLAUDE_MODEL) from the .env file
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
model = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

if not api_key:
    raise SystemExit("ANTHROPIC_API_KEY is missing. Check your .env file.")

client = Anthropic(api_key=api_key)

response = client.messages.create(
    model=model,
    max_tokens=200,
    messages=[
        {
            "role": "user",
            "content": "Say hello and introduce yourself in one sentence.",
        }
    ],
)

print(f"Model: {model}")
print(f"Claude says: {response.content[0].text}")