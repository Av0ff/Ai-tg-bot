# Ai-tg-bot

This is a Telegram support bot powered by an LLM and RAG. It answers questions using uploaded documents, keeps ticket history in SQLite, and escalates to a specialist when needed.

## Requirements

- Python 3.10+
- OpenAI API key
- Telegram bot token

## Data folders

- `data/assistant_profile.txt`: describe the bot context (company, domain, topic, tone). It is used both as the `/start` greeting and as context in the system prompt. An example is provided in this file.
- `data/docs/`: place your PDF/DOCX/TXT files here for ingestion.
- `data/parsed/faq_pairs.json`: auto-generated normalized Q/A pairs.
- `data/chroma/`: local Chroma vector store (auto-generated).

## Ticket statuses and storage

- Status values: `open`, `needs_agent`, `resolved`.
- `tickets` table: ticket metadata (user, status, timestamps).
- `ticket_messages` table: chat history per ticket.
- The SQLite DB lives in `app.db`.
- If the assistant can resolve the issue, the user closes it via the "Resolved" button.
- If the user wants a human, they can press "Need specialist".
- If the user asks something outside the context and the assistant cannot answer, it auto-sets `needs_agent`.
- There is no real specialist workflow yet. This is a pet project to demonstrate DB usage, Telegram bot flow, RAG search, and automation with LLMs. Implementing the specialist workflow is left for real-world needs.

## Vector search (RAG)

Documents are embedded and stored in a local Chroma vector database. At runtime the bot embeds the user query, runs a cosine similarity search to retrieve top chunks, and appends them to the system prompt as context.

## Debug scripts

You can use the Bash snippets in `scripts/debug_queries.txt` to inspect the SQLite database and the vector store contents.

## RAG ingestion

1) Put documents into `data/docs/`.
2) Run ingestion (reset + parse + index):
   ```bash
   python -m app.ingest
   ```
3) Start the bot:
   ```bash
   python -m app.bot
   ```

Ingest modes:
- default (no flags): reset + parse + index
- `--parse`: only normalize documents into Q/A pairs
- `--index`: only index existing Q/A pairs into Chroma
- `--reset`: clear the vector store before indexing

Optional ingestion flags:
```bash
python -m app.ingest --parse
python -m app.ingest --index
python -m app.ingest --reset
```

Environment variables (optional):
```
DOCS_DIR=./data/docs
PAIRS_JSON=./data/parsed/faq_pairs.json
CHROMA_PATH=./data/chroma
MAX_WORDS_PER_CHUNK=300
CHUNK_OVERLAP_WORDS=50
EMBED_BATCH_SIZE=32
OPENAI_EMBED_MODEL=text-embedding-3-small
ASSISTANT_PROFILE_PATH=./data/assistant_profile.txt
```

## Install and run (Windows PowerShell)

1) Clone the repo and go to the project folder.
2) Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3) Create a `.env` file in the project root with:
   ```
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   # optional
   OPENAI_MODEL=gpt-4o-mini
   ```
4) Update `data/assistant_profile.txt`, add documents to `data/docs/`, then run ingestion:
   ```bash
   python -m app.ingest
   ```
5) Run the bot:
   ```bash
   python -m app.bot
   ```

## Install and run (Linux/macOS)

1) Clone the repo and go to the project folder.
2) Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3) Create a `.env` file in the project root with:
   ```
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   # optional
   OPENAI_MODEL=gpt-4o-mini
   ```
4) Update `data/assistant_profile.txt`, add documents to `data/docs/`, then run ingestion:
   ```bash
   python -m app.ingest
   ```
5) Run the bot:
   ```bash
   python -m app.bot
   ```

The SQLite database file (`app.db`) will be created automatically in the project root.
Logs are written to `bot.log` in the project root.
