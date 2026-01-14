# Ai-tg-bot

This is a simple Telegram bot for a stationery online store. It answers customer questions using a small FAQ and switches tickets to a specialist when it is not confident. The bot also stores ticket history in SQLite so the conversation has context.

FAQ topics included:
- Delivery options
- Order status lookup
- Return policy
- Bulk discounts
- Company invoices

## Install and run

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
4) Run the bot:
   ```bash
   python -m app.bot
   ```

The SQLite database file (`app.db`) will be created automatically in the project root.
