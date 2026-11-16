# AI Service Desk Agent

An IT help-desk assistant for a fictional company (Pinecrest Supply Co.), built with Python, the Anthropic Claude API and FastAPI. It answers employee questions from a knowledge base, opens and looks up support tickets through tool calling, and defends against prompt injection and personal-data leaks.

This is a portfolio project. The company and all data are fictional.

## What it does

- **Grounded answers:** finds the most relevant help articles and answers only from them. If the answer isn't in the knowledge base, it says so and offers a ticket.
- **Tool calling:** Claude decides when to call `create_ticket` or `get_ticket_status`, which read and write a SQLite database.
- **Guardrails:** prompt-injection blocking, PII masking (emails, phones, SSNs, card numbers) before anything reaches the model, and validation of tool arguments.
- **REST API:** a FastAPI service with per-session conversation memory and auto-generated docs.
- **Evaluation:** a repeatable test script that scores answers, tool use and guardrails.

## How it works

```
Employee message
   |
   |-- guardrails: injection check  -> refuse (the model is never called)
   |-- guardrails: mask PII
   |-- kb.py: keyword search        -> top 2 articles
   v
Claude (system prompt + articles + tool definitions)
   |-- answers from the articles
   |-- or calls a tool -> tickets.py (SQLite) -> result goes back to Claude
   v
Reply + source article
```

## Quick start (Windows PowerShell)

```
git clone https://github.com/rakeshvarmakota/ai-service-desk-agent.git
cd ai-service-desk-agent
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and add your Anthropic API key. Then either:

```
python ask.py                  # chat in the terminal
uvicorn api:app --reload       # run the API, then open http://127.0.0.1:8000/docs
```

## API

| Endpoint | Purpose |
|---|---|
| `POST /chat` | Send `{"message": "...", "session_id": "..."}`. Omit `session_id` to start a conversation; send it back to continue. |
| `GET /tickets/{id}` | Read a ticket directly from the database. |
| `GET /health` | Check that the server is running. |

Example:

```
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/chat -ContentType "application/json" -Body '{"message": "How do I reset my password?"}'
```

## Evaluation

```
python eval.py
```

Runs 12 test conversations across four categories (knowledge base, tools, guardrails, robustness) against a temporary database and writes the results to [`eval_results.md`](eval_results.md). Checks include: the right article was retrieved, the right tool was called, raw personal data never reached the model, and attack prompts did not leak instructions. LLM output varies between runs, so a borderline test can flip.

## Security design and known limitations

- **Defense in depth:** a keyword filter blocks common injection phrases before the model is called; the system prompt separately tells the model to treat article text as data and never reveal its instructions; tool arguments are validated before they touch the database.
- **The injection filter is pattern-based.** A rephrased attack can get past it, which is why the robustness tests exist and why the model-level rules matter.
- **PII masking uses regular expressions.** It catches emails, phone numbers, SSNs and Luhn-valid card numbers, but not names or addresses.
- **Retrieval is keyword-based,** not embedding-based. It works for a small knowledge base but would not scale.
- **Sessions live in memory** and the API has no authentication or rate limiting.

## Project structure

```
ask.py          conversation loop, Claude call, tool-use loop
kb.py           loads articles and finds the best matches
tickets.py      SQLite ticket database
guardrails.py   injection check, PII masking, tool-input validation
api.py          FastAPI service
eval.py         evaluation script
knowledge_base/ help articles (Markdown)
```

## Next steps

Embedding-based retrieval, authentication and rate limiting, persistent sessions, Docker packaging, and a larger evaluation set.
