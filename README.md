# Peacy - The AI Mediator

Peacy is an AI-powered mediator designed for group chats. Built using Python, Peacy leverages OpenAI’s language models (via the Groq API) to generate thoughtful, empathetic responses while maintaining a persistent memory of conversations using ChromaDB and PostgreSQL. Peacy listens to group discussions, learns from interactions, and responds only when activated by a wake word (e.g., "Peacy", "PC", etc.), continuously evolving its understanding of the community.

## Features

- **Persistent Memory**:  
  Peacy stores conversation data in a vector index using ChromaDB, ensuring previous interactions are remembered across restarts.

- **Structured User Profiles**:  
  Critical user data (such as profiles) is stored in PostgreSQL, allowing Peacy to personalize responses without echoing sensitive information.

- **Dynamic Context-Aware Responses**:  
  By incorporating conversation history into its prompts, Peacy generates smooth, context-aware replies.

- **Wake Word Activation**:  
  The bot responds only when a wake word (e.g., "Peacy", "PC", "Peacccy") is detected in a message, preventing unnecessary interruptions.

- **Background Tasks**:  
  Peacy periodically summarizes group chat conversations through background tasks.

## Requirements

Please refer to the [`requirements.txt`](requirements.txt) file for a complete list of dependencies:

```
python-telegram-bot
openai
chromadb
psycopg2-binary
sentence_transformers
APScheduler
rich
python-dotenv
nest_asyncio
```

## Installation

1. **Clone the Repository:**

```bash
git clone https://github.com/yourusername/peacy.git
cd peacy
```

2. **Set Up a Virtual Environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. **Install Dependencies:**

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file (or update `config.py`) with the following environment variables:

```
TELEGRAM_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
PG_CONNECTION_STRING=dbname=peacy_db user=peacy_admin password=admin host=localhost port=5432
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## Usage

To run the bot, execute:

```bash
python bot.py
```

Peacy will:

- Initialize the PostgreSQL database (creating tables for messages and user profiles if they don’t exist).
- Seed initial memory if the vector index is empty.
- Start background tasks (e.g., conversation summarization).
- Listen for messages containing specified wake words.
- Update user profiles silently when users introduce themselves.
- Generate smooth, context-aware responses based on conversation history.

## Project Structure

```
peacy/
├── bot.py                 # Main bot file (Telegram integration and core logic)
├── config.py              # Configuration file for environment variables
├── db_manager.py          # Database management: initializing and logging to PostgreSQL
├── memory_manager.py      # Persistent memory handling with ChromaDB and SentenceTransformer
├── background_tasks.py    # Background tasks (conversation summarization using APScheduler)
├── requirements.txt       # Python package dependencies
└── README.md              # This file
```

## Customization

### Response Generation

Modify the `sync_generate_response` function in `bot.py` to adjust the system prompt or model parameters for different response styles.

### Memory & Profile Integration

The bot silently updates and retrieves user profile data from PostgreSQL, integrating it into the memory context for responses. Adjust this logic in the `handle_message` function as needed.

### Wake Words

Update the `WAKE_WORDS` list in `bot.py` to change the keywords that trigger Peacy.

## Graceful Shutdown

Peacy uses asynchronous programming with `asyncio` and `nest_asyncio` for smooth operation. To stop the bot, press `Ctrl+C`. The code attempts to handle shutdown gracefully; however, you might see a message like "Cannot close a running event loop" during a forced shutdown, which is expected.

## License

This project is licensed under the MIT License.

