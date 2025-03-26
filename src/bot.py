import logging
# Suppress noisy logs from SentenceTransformers
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

import nest_asyncio
nest_asyncio.apply()

import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import asyncio
import pytz
import openai
import spacy
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ChatMemberHandler,
    ContextTypes,
    filters,
    JobQueue
)
from rich.console import Console
from rich.logging import RichHandler

from config import config
from text_analysis import analyze_sentiment, extract_location, extract_person_name

# Import memory functions and DB helpers; note that memory_manager's expensive init is now deferred.
from memory_manager import add_memory, retrieve_memory, seed_memory_dynamic, init_memory_manager
from db_manager import (
    init_db,
    log_message,
    update_user_profile,
    get_user_profile,
    get_conversation_summary,
    update_conversation_summary_in_db
)
from background_tasks import start_scheduler

# --- Define the LangChain prompt template (we delay initializing LLM and memory) ---
from langchain.prompts import PromptTemplate

prompt_template = PromptTemplate(
    input_variables=["conversation_summary", "user_input"],
    template=(
        "You are Peacy, a friendly and supportive AI guided by the core values of love, peace, and joy. "
        "You treat every conversation with care and empathy, remembering personal details like names, locations, and emotional states. "
        "You never judge or criticize; instead, you listen and help resolve conflicts as a trusted friend. "
        "Occasionally, use a friendly emoji to add warmth to your responses, but do so sparingly. "
        "Your replies should be direct, succinct, and focus solely on answering the current query without echoing the internal context. "
        "Use the context only to maintain continuity and a personal connection.\n\n"
        "Context (for internal use only): {conversation_summary}\n"
        "User: {user_input}\n"
        "Peacy:"
    )
)

# Globals to be initialized later.
llm = None
response_chain = None
conversation_memory = None

# --- Define wake words ---
WAKE_WORDS = [
    "peacy", "pc", "peacybot", "peacyai", "peacy-ai",
    "peacy-bot", "peacey", "peaceybot", "peaceyai",
    "peacey-ai", "peacey-bot"
]

def contains_wake_word(text: str) -> bool:
    return any(w in text.lower() for w in WAKE_WORDS)

# --- Define the chat member update handler ---
async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        new_member = update.chat_member.new_chat_member.user
        user_id = new_member.id
        username = new_member.username or ""
        full_name = new_member.full_name or ""
        profile_info = f"{full_name} (username: {username})" if username else full_name
        update_user_profile(user_id, username, profile_info)
        logger.info(f"Updated user info for {user_id}: {profile_info}")
    except Exception as e:
        logger.exception(f"Error updating user info: {e}")

# --- Response generation using the (to-be-initialized) LangChain components ---
async def generate_response(user_input: str, conversation_summary: str = "") -> str:
    inputs = {"conversation_summary": conversation_summary, "user_input": user_input}
    try:
        result = await asyncio.to_thread(response_chain.invoke, inputs)
        if hasattr(result, "content"):
            return result.content.strip()
        return str(result).strip()
    except Exception as e:
        if "401" in str(e) or "invalid_api_key" in str(e):
            logger.error(f"Authentication error: {e}")
            return "Sorry, I'm having trouble authenticating. Please check my configuration."
        else:
            logger.exception("Error generating response:")
            return "Sorry, I encountered an error generating a response."

# --- Message handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_message = update.message.text.strip()
    if not contains_wake_word(user_message):
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    logger.info(f"Received message from {user_id} in chat {chat_id}: {user_message}")

    # Update user profile from Telegram data.
    telegram_user = update.effective_user
    username = telegram_user.username or ""
    full_name = telegram_user.full_name or ""
    profile_info = f"{full_name} (username: {username})" if username else full_name
    update_user_profile(user_id, username, profile_info)

    # Dynamic extraction of personal information.
    extracted_name = extract_person_name(user_message)
    extracted_location = extract_location(user_message)
    sentiment = analyze_sentiment(user_message)

    # Retrieve current profile and update if a new name is detected.
    current_profile = get_user_profile(user_id)
    stored_name = current_profile[0] if current_profile and current_profile[0] else ""
    if extracted_name and (not stored_name or extracted_name.lower() != stored_name.lower()):
        new_profile_info = f"Location: {extracted_location}, Sentiment: {sentiment}"
        update_user_profile(user_id, extracted_name, new_profile_info)
        logger.info(f"Updated profile for {user_id} with new name: {extracted_name}")

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, log_message, chat_id, user_id, user_message)

    # Update dynamic conversation memory.
    await asyncio.to_thread(conversation_memory.save_context, {"input": user_message}, {"output": ""})
    dynamic_summary = conversation_memory.load_memory_variables({})["chat_history"]

    if isinstance(dynamic_summary, list):
        dynamic_summary = "\n".join(str(item) for item in dynamic_summary)

    retrieved = retrieve_memory(user_message, n_results=3)
    retrieved_text = f"Relevant past interactions: {retrieved}\n" if retrieved else ""

    persistent_summary = get_conversation_summary(chat_id)

    combined_summary = ""
    if persistent_summary:
        combined_summary += f"Persistent conversation summary: {persistent_summary}\n"
    combined_summary += retrieved_text
    combined_summary += dynamic_summary

    profile = get_user_profile(user_id)
    if profile and profile[0]:
        combined_summary = f"User: {profile[0]}.\n" + combined_summary

    MAX_CONTEXT_LENGTH = 2048
    if len(combined_summary) > MAX_CONTEXT_LENGTH:
        combined_summary = combined_summary[-MAX_CONTEXT_LENGTH:]

    logger.info(f"Conversation summary for response: {combined_summary}")

    reply = await generate_response(user_message, combined_summary)
    logger.info(f"Generated reply: {reply}")

    await update.message.reply_text(reply)
    await loop.run_in_executor(None, log_message, chat_id, "Peacy", reply)
    await loop.run_in_executor(None, add_memory, user_message, {"role": "user"})
    await loop.run_in_executor(None, add_memory, reply, {"role": "peacy"})

    update_conversation_summary_in_db(chat_id, combined_summary)

# --- Main initialization using sequential logging (no spinners) ---
async def main():
    global llm, response_chain, conversation_memory

    loop = asyncio.get_event_loop()
    console = Console()

    console.log("[cyan]Initializing PostgreSQL database...[/cyan]")
    await loop.run_in_executor(None, init_db)
    console.log("[green]Database initialized.[/green]")

    console.log("[cyan]Loading spaCy model...[/cyan]")
    # spaCy model is loaded at import time.
    console.log("[green]spaCy model loaded.[/green]")

    console.log("[cyan]Initializing Memory Manager...[/cyan]")
    await loop.run_in_executor(None, init_memory_manager)
    # Removed duplicate log here:
    # console.log("[green]Memory Manager initialized.[/green]")

    console.log("[cyan]Initializing Language Model and conversation memory...[/cyan]")
    from langchain_community.chat_models import ChatOpenAI  # delayed import
    llm = ChatOpenAI(
        openai_api_base="https://api.groq.com/openai/v1",
        openai_api_key=config.GROQ_API_KEY,
        model_name="llama-3.3-70b-versatile",
        temperature=0.7,
    )
    response_chain = prompt_template | llm
    from langchain.memory import ConversationSummaryMemory
    conversation_memory = ConversationSummaryMemory(
        llm=llm,
        max_token_limit=1024,
        memory_key="chat_history",
        return_messages=True,
        ai_prefix="Peacy",
    )
    console.log("[green]Language Model initialized.[/green]")

    console.log("[cyan]Seeding memory...[/cyan]")
    await loop.run_in_executor(None, seed_memory_dynamic)
    console.log("[green]Memory seeded.[/green]")

    console.log("[cyan]Starting background tasks...[/cyan]")
    start_scheduler()  # runs in its own thread
    console.log("[green]Background tasks started.[/green]")

    # Create a JobQueue for Telegram.
    job_queue = JobQueue()
    job_queue.scheduler._timezone = pytz.utc

    # Build the Telegram application.
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).job_queue(job_queue).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER))

    logger.info("Peacy is running...")
    await application.run_polling()

if __name__ == '__main__':
    # Configure logging once at startup.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()]
    )
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown gracefully via KeyboardInterrupt.")
    except RuntimeError as e:
        if "Cannot close a running event loop" in str(e):
            logger.info("Bot shutdown gracefully.")
        else:
            raise
# --- End Updated bot.py ---
