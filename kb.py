"""Loads the knowledge base articles and finds the ones that best match a question."""
import re
from pathlib import Path

KB_FOLDER = Path(__file__).parent / "knowledge_base"

# Common words that don't help with matching.
STOP_WORDS = {
    "a", "an", "and", "are", "can", "do", "does", "for", "how", "i", "if", "in",
    "is", "it", "my", "of", "on", "or", "the", "to", "what", "when", "with", "you", "your",
}


def tokenize(text):
    """Turn text into a list of lowercase words, without the common words."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [word for word in words if word not in STOP_WORDS]


def load_articles():
    """Read every .md file in the knowledge base folder."""
    articles = []
    for path in sorted(KB_FOLDER.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        articles.append({"title": title, "text": text, "file": path.name})
    return articles


def search(question, top_k=2):
    """Return the top_k articles that share the most words with the question."""
    question_words = set(tokenize(question))
    scored = []
    for article in load_articles():
        title_words = tokenize(article["title"])
        body_words = tokenize(article["text"])
        # A match in the title counts 3 times as much as a match in the body.
        score = sum(3 for word in title_words if word in question_words)
        score += sum(1 for word in body_words if word in question_words)
        if score > 0:
            scored.append((score, article))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [article for score, article in scored[:top_k]]


if __name__ == "__main__":
    # Quick test: run "python kb.py" to see which articles match.
    for question in ["How do I reset my password?", "My VPN is not working", "What is the lunch menu?"]:
        matches = search(question)
        print(question, "->", [article["title"] for article in matches])