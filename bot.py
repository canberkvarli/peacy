import nest_asyncio
nest_asyncio.apply()

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
import openai
import asyncio
import concurrent.futures
import pytz
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,

    MessageHandler,
    ContextTypes,
    filters,
    JobQueue
)
import spacy
from config import TELEGRAM_TOKEN, GROQ_API_KEY, PG_CONNECTION_STRING
from memory_manager import add_memory, retrieve_memory, seed_memory
from db_manager import init_db, log_message, update_user_profile, get_user_profile, get_conversation_summary, update_conversation_summary_in_db
from background_tasks import start_scheduler
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import spaCy for NLP-based entity recognition.
nlp = spacy.load("en_core_web_sm")

# Configure OpenAI (Groq) API.
openai.api_key = GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
console = Console()

# Define wake words so that Peacy only responds when activated.
WAKE_WORDS = ["peacy", "pc", "peacybot", "peacyai", "peacy-ai", "peacy-bot", "peacey", "peaceybot", "peaceyai", "peacey-ai", "peacey-bot"]

def contains_wake_word(text: str) -> bool:
    lower_text = text.lower()
    return any(w in lower_text for w in WAKE_WORDS)

# Synchronous function to generate a reply using OpenAI.
def sync_generate_response(user_input: str, memory_context: str = "") -> str:
    # Modified system prompt to instruct the model to avoid repetitive greetings.
    system_prompt = (
        "You are Peacy, a kind and peaceful AI mediator."
        "You follow Nonviolent Communication (NVC) principles and keep a subtle memory of past conversations. "
        "When generating a reply, do not start with a greeting such as 'Hello' or 'Hi' if the conversation is ongoing. "
        "Focus on directly addressing the user's message and maintaining a smooth, natural conversation flow."
        "Build personal connections and offer empathetic responses. "
        "Remember to be supportive, understanding, and conflict-free."
        )
    # Build the prompt using any provided memory context plus the current user input.
    prompt = f"{memory_context}\nUser: {user_input}\nPeacy:"
    try:
        response = openai.ChatCompletion.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        reply = response.choices[0].message.content.strip()
        logger.debug(f"Groq API response: {reply}")
    except Exception as e:
        logger.exception("Error during generate_response:")
        reply = "Sorry, I couldn't generate a response at the moment."
    return reply


# Asynchronous wrapper.
async def generate_response(user_input: str, memory_context: str = "") -> str:
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        reply = await loop.run_in_executor(pool, sync_generate_response, user_input, memory_context)
    return reply

# A helper function to silently extract a person's name from a message using spaCy.
def extract_person_name(text: str) -> str:
    doc = nlp(text)
    # Return the first PERSON entity found.
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return ""

# General message handler.
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text.strip()
    # Only process if a wake word is present.
    if not contains_wake_word(user_message):
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    logger.info(f"Received message from {user_id} in chat {chat_id}: {user_message}")

    # Dynamically attempt to extract a name from the message if the user's profile is not set.
    profile = get_user_profile(user_id)
    if (not profile) or (not profile[0]):
        name = extract_person_name(user_message)
        if name:
            update_user_profile(user_id, name)
            # Optionally, send a very brief confirmation.
            await update.message.reply_text("Thanks, I'll keep that in mind.")

    # Log the user's message.
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, log_message, chat_id, user_id, user_message)

    # Retrieve and update conversation summary.
    conv_summary = get_conversation_summary(chat_id)
    updated_summary = (conv_summary + " " + user_message) if conv_summary else user_message
    update_conversation_summary_in_db(chat_id, updated_summary)

    # Include the conversation summary in the memory context.
    memory_context = f"Conversation summary: {updated_summary}\n"
    # Also include user profile info silently.
    profile = get_user_profile(user_id)
    if profile and profile[0]:
        memory_context = f"User info: {profile[0]}.\n" + memory_context

    logger.info(f"Memory context for response: {memory_context}")

    # Generate a reply.
    reply = await generate_response(user_message, memory_context)
    logger.info(f"Generated reply: {reply}")

    # Send the reply.
    await update.message.reply_text(reply)
    # Log the reply and add both the incoming message and reply to persistent memory.
    await loop.run_in_executor(None, log_message, chat_id, "Peacy", reply)
    await loop.run_in_executor(None, add_memory, user_message, {"role": "user"})
    await loop.run_in_executor(None, add_memory, reply, {"role": "peacy"})

# Main initialization.
async def main():
    loop = asyncio.get_event_loop()
    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        transient=True,
        console=console
    ) as progress:
        db_task = progress.add_task("[cyan]Initializing PostgreSQL database...", total=None)
        await loop.run_in_executor(None, init_db)
        progress.update(db_task, description="[green]Database initialized.[/green]")

        seed_task = progress.add_task("[cyan]Seeding memory...", total=None)
        await loop.run_in_executor(None, seed_memory)
        progress.update(seed_task, description="[green]Memory seeded.[/green]")

        sched_task = progress.add_task("[cyan]Starting background tasks...", total=None)
        start_scheduler()  # Runs in its own thread.
        progress.update(sched_task, description="[green]Background tasks started.[/green]")

    job_queue = JobQueue()
    job_queue.scheduler._timezone = pytz.utc

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).job_queue(job_queue).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Peacy is running...")
    await application.run_polling()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
