import nest_asyncio
nest_asyncio.apply()

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"
import logging
import openai
import asyncio
import concurrent.futures
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    JobQueue
)
from config import TELEGRAM_TOKEN, GROQ_API_KEY
from memory_manager import add_memory, retrieve_memory, seed_memory
from db_manager import init_db, log_message
from background_tasks import start_scheduler
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
import pytz

# Configure Groq API.
openai.api_key = GROQ_API_KEY
openai.api_base = "https://api.groq.com/openai/v1"

# Configure logging.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)
console = Console()

def sync_generate_response(user_input: str, memory_context: str = "") -> str:
    system_prompt = (
        "You are Peacy, a kind and peaceful AI mediator in a Telegram group. "
        "You follow Nonviolent Communication (NVC) principles, act empathetically, and remember past conversations to build personal relations."
    )
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

async def generate_response(user_input: str, memory_context: str = "") -> str:
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        reply = await loop.run_in_executor(pool, sync_generate_response, user_input, memory_context)
    return reply

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Hello! I am Peacy, your friendly AI mediator.")

async def debug_update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("DEBUG: Received update: %s", update)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_message = update.message.text
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    logger.info(f"Received message from {user_id} in chat {chat_id}: {user_message}")
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, log_message, chat_id, user_id, user_message)
    memory_context = await loop.run_in_executor(None, retrieve_memory, user_message, 3)
    logger.info(f"Retrieved memory context: {memory_context}")
    
    reply = await generate_response(user_message, memory_context)
    logger.info(f"Generated reply: {reply}")
    
    await update.message.reply_text(reply)
    
    await loop.run_in_executor(None, log_message, chat_id, "Peacy", reply)
    await loop.run_in_executor(None, add_memory, user_message, {"role": "user"})
    await loop.run_in_executor(None, add_memory, reply, {"role": "peacy"})

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
        start_scheduler()  # Background tasks run in their own thread.
        progress.update(sched_task, description="[green]Background tasks started.[/green]")
    
    # Create a JobQueue normally.
    from telegram.ext import JobQueue
    job_queue = JobQueue()
    # Force its scheduler timezone to pytz.utc.
    job_queue.scheduler._timezone = pytz.utc
    
    # Build the application using the pre-configured job queue.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).job_queue(job_queue).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.ALL, debug_update_handler))
    
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