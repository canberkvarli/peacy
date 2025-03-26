# Peacy - The AI Mediator

Peacy is an AI-powered mediator designed for group chats. Built using Python, Peacy leverages OpenAI’s language models (via the Groq API) to generate thoughtful, empathetic responses while maintaining a persistent memory of conversations using ChromaDB and PostgreSQL. Peacy listens to group discussions, learns from interactions, and responds only when activated by a wake word (e.g., "Peacy", "PC", etc.), continuously evolving its understanding of the community.

## Features

### Persistent Memory & Vector Search
- Uses a Chroma vector store (via LangChain and ChromaDB) to store and retrieve conversation memories for context-aware responses.

### Structured User Profiles
- Stores user data and conversation summaries in PostgreSQL, enabling personalized interactions and continuity across sessions.

### Dynamic, Context-Aware Responses
- Integrates conversation history into prompt templates using LangChain (with the ChatOpenAI interface) to generate smooth, context-sensitive replies.

### Wake Word Activation
- Listens for a predefined set of wake words (e.g., "Peacy", "PC", etc.) to trigger a response, preventing unnecessary interruptions.

### Background Tasks & Scheduled Analysis
- Periodically summarizes conversations and performs detailed analysis (sentiment, entity extraction) using background tasks scheduled via APScheduler.

### Reset & Maintenance Tools
- Includes scripts to reset the Chroma vector store and PostgreSQL tables for easy maintenance and testing.

## Requirements

Peacy uses Pipenv for dependency management. The following packages are required (see the [Pipfile](Pipfile) for full details):

- python-telegram-bot
- openai
- chromadb
- psycopg2-binary
- sentence-transformers
- apscheduler
- rich
- python-dotenv
- nest-asyncio
- spacy
- pytz
- langchain
- langchain_community
- langchain-huggingface
- langchain-chroma

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/peacy.git
cd peacy
```

### 2. Install Pipenv

```bash
pip install pipenv
```

### 3. Install Dependencies with Pipenv

```bash
pipenv install
```

This command creates a virtual environment and installs all required packages from the Pipfile and Pipfile.lock.

### 4. Activate the Virtual Environment

```bash
pipenv shell
```

## Configuration

Create a `.env` file in the project root and set the following environment variables:

```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
GROQ_API_KEY=your_groq_api_key_here
OPEN_AI_API_KEY=your_open_ai_api_key_here
PG_CONNECTION_STRING="your_connection_string_here"
CHROMA_PERSIST_DIRECTORY=./chroma_db
PINECONE_API_KEY=your_pinecone_api_key_here # if using Pinecone
ENV=development
```

Ensure these variables are correctly configured for your deployment.

## Usage

To run the bot locally (with the virtual environment activated):

```bash
python src/bot.py
```

## Runtime Behavior

### Database Initialization
- Initializes PostgreSQL database on startup (creates tables for messages, users, and summaries).

### Memory Seeding
- Seeds the Chroma vector store if empty to kickstart context building.

### Background Tasks
- Scheduled tasks for summarization and analysis using APScheduler.

### Wake Word Activation
- Responds only when messages contain designated wake words.

## Storage Reset

To reset Chroma and PostgreSQL storage, run:

```bash
python reset_storage.py
```

This script:
- Removes Chroma persistence directory (if exists).
- Drops PostgreSQL tables for messages, users, and conversation summaries.

## Project Structure

```bash
peacy/
├── src/
│   ├── __init__.py
│   ├── bot.py                # Main bot file
│   ├── config.py             # Loads environment variables
│   ├── db_manager.py         # PostgreSQL DB initialization & logging
│   ├── memory_manager.py     # Persistent memory handling (ChromaDB)
│   ├── background_tasks.py   # Scheduled summarization & analysis tasks
│   └── text_analysis.py      # Sentiment analysis & entity extraction
│   └── reset_storage.py      # Storage reset utilities
├── Pipfile                   # Pipenv dependencies
├── Pipfile.lock              # Dependency versions
├── .env                      # Environment variable definitions
├── .gitignore
├── README.md                 # Project documentation
```

## Customization

### Response Generation
- Modify the prompt template and parameters in `src/bot.py`.

### Memory & Profile Integration
- Adjust logic in `src/db_manager.py` and `src/memory_manager.py`.

### Wake Words
- Customize the wake words in `src/bot.py`.

## Graceful Shutdown

Uses asynchronous programming (`asyncio` and `nest_asyncio`) for smooth operation. To stop Peacy, press `Ctrl+C`. A graceful shutdown is designed, though forced shutdowns might display messages like "Cannot close a running event loop".

