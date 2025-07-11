import os
import anthropic

from dotenv import load_dotenv
load_dotenv()

def test_claude():
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = client.messages.create(
        model="claude-3-haiku-20240307",  # Use Haiku (fast, cheap) for testing
        max_tokens=100,
        temperature=0.3,
        messages=[
            {"role": "user", "content": "List 3 high-protein lunch ideas for someone who is cutting weight."}
        ]
    )

    print("✅ Claude responded:")
    print(response.content[0].text.strip())

if __name__ == "__main__":
    test_claude()
