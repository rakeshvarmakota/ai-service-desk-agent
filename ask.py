"""Service desk assistant: answers from the knowledge base and can open or look up tickets."""
import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

import tickets
from kb import search

load_dotenv()

MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-5-5")

SYSTEM_PROMPT = """You are the IT service desk assistant for Pinecrest Supply Co.
Answer questions using ONLY the knowledge base articles provided in each message.
If the articles do not contain the answer, say you don't know and offer to open a ticket.

You have two tools:
- create_ticket: use it only when the employee asks for a ticket (or agrees to one).
  You need their name, a category and a one-sentence summary. If any are missing, ask for them first.
- get_ticket_status: use it when the employee gives a ticket number and wants an update.

After using a tool, tell the employee the result in plain words (include the ticket number).
Keep answers short. When you used an article, end with its title."""

TOOLS = [
    {
        "name": "create_ticket",
        "description": "Open a new IT support ticket for an employee.",
        "input_schema": {
            "type": "object",
            "properties": {
                "employee": {"type": "string", "description": "The employee's name"},
                "category": {"type": "string", "enum": tickets.CATEGORIES},
                "summary": {"type": "string", "description": "One sentence describing the problem"},
            },
            "required": ["employee", "category", "summary"],
        },
    },
    {
        "name": "get_ticket_status",
        "description": "Look up an existing ticket by its number.",
        "input_schema": {
            "type": "object",
            "properties": {"ticket_id": {"type": "integer", "description": "The ticket number"}},
            "required": ["ticket_id"],
        },
    },
]


def run_tool(name, tool_input):
    """Run the tool Claude asked for and return the result."""
    if name == "create_ticket":
        return tickets.create_ticket(**tool_input)
    if name == "get_ticket_status":
        return tickets.get_ticket(tool_input["ticket_id"])
    return {"error": f"Unknown tool: {name}"}


def build_prompt(question, articles):
    """Put the matching articles and the question into one message."""
    parts = ["Knowledge base articles:"]
    for article in articles:
        parts.append(f"<article title=\"{article['title']}\">\n{article['text']}\n</article>")
    if not articles:
        parts.append("(no matching articles found)")
    parts.append(f"Employee message: {question}")
    return "\n\n".join(parts)


def answer(question, history, client=None):
    """Answer one message. 'history' keeps the whole conversation so Claude remembers earlier turns."""
    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise SystemExit("ANTHROPIC_API_KEY is missing. Check your .env file.")
        client = Anthropic(api_key=api_key)

    articles = search(question)
    sources = [article["file"] for article in articles]
    history.append({"role": "user", "content": build_prompt(question, articles)})

    for _ in range(5):  # safety limit so the loop can never run forever
        response = client.messages.create(
            model=MODEL, max_tokens=500, system=SYSTEM_PROMPT, tools=TOOLS, messages=history
        )
        history.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            text = "".join(block.text for block in response.content if block.type == "text")
            return text, sources

        # Claude asked to use one or more tools: run them and send the results back.
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  [tool used: {block.name} {block.input}]")
                result = run_tool(block.name, block.input)
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}
                )
        history.append({"role": "user", "content": results})

    return "Sorry, I could not finish that request. Please try again.", sources


if __name__ == "__main__":
    print("Service desk assistant. Type a question, or 'quit' to stop.")
    history = []
    while True:
        question = input("\nYou: ").strip()
        if question.lower() in {"quit", "exit", ""}:
            break
        reply, sources = answer(question, history)
        print(f"\nAssistant: {reply}")
        print(f"(articles searched: {sources})")