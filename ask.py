"""Ask the service desk assistant a question. It answers only from the knowledge base."""
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from kb import search

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

SYSTEM_PROMPT = """You are the IT service desk assistant for Pinecrest Supply Co.
Answer the employee's question using ONLY the knowledge base articles provided.
If the articles do not contain the answer, say you don't know and suggest opening a ticket.
Keep the answer short and end with the title of the article you used."""


def build_prompt(question, articles):
    """Put the matching articles and the question into one message."""
    parts = ["Knowledge base articles:"]
    for article in articles:
        parts.append(f"<article title=\"{article['title']}\">\n{article['text']}\n</article>")
    if not articles:
        parts.append("(no matching articles found)")
    parts.append(f"Employee question: {question}")
    return "\n\n".join(parts)


def answer(question):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SystemExit("ANTHROPIC_API_KEY is missing. Check your .env file.")

    articles = search(question)
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_prompt(question, articles)}],
    )
    sources = [article["file"] for article in articles]
    return response.content[0].text, sources


if __name__ == "__main__":
    print("Service desk assistant. Type a question, or 'quit' to stop.")
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"quit", "exit", ""}:
            break
        reply, sources = answer(question)
        print(f"\nAssistant: {reply}")
        print(f"(articles searched: {sources})")