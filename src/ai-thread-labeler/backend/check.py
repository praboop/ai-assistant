import os
from openai import OpenAI
from openai.types.chat import ChatCompletionMessage

# Load your API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found in environment variables.")

client = OpenAI(api_key=api_key)

try:
    # List available models
    print("📦 Available models:")
    models = client.models.list()
    for model in models.data:
        print(f"- {model.id}")

    # Try sending a test message to GPT-4-Turbo
    print("\n🤖 Sending test message to gpt-4-turbo...")
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": "Say hello!"}],
        temperature=0.2,
    )

    reply: ChatCompletionMessage = response.choices[0].message
    print(f"\n✅ GPT-4-Turbo replied: {reply.content}")

except Exception as e:
    print(f"\n❌ Error: {e}")
