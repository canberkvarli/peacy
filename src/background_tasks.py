# background_tasks.py
import psycopg2
from config import config
from rich.console import Console
from text_analysis import extract_person_name, extract_location, analyze_sentiment
from db_manager import update_user_profile, get_user
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

console = Console()

BOT_ID = None

def summarize_conversations():
    console.log("[bold blue]Starting summarization of conversations...[/bold blue]")
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("""
        SELECT chat_id, array_agg(message_text ORDER BY timestamp) as messages
        FROM messages
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        GROUP BY chat_id
    """)
    rows = cur.fetchall()
    for chat_id, messages in rows:
        summary = " ".join(messages)
        console.log(f"[bold green]Chat {chat_id} summary:[/bold green] {summary[:100]}...")
    cur.close()
    conn.close()

def analyze_and_learn():
    """
    Extract key details from recent messages and update user profiles using NLP.
    Only human users are processed—the bot’s own ID is skipped.
    Manual (explicit) updates are preserved.
    """
    console.log("[bold blue]Starting detailed analysis of conversations...[/bold blue]")
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, message_text
        FROM messages
        WHERE timestamp > NOW() - INTERVAL '1 hour'
    """)
    rows = cur.fetchall()

    user_data = {}
    for user_id, message_text in rows:
        # Skip messages from the bot.
        # if str(user_id) == BOT_ID:
        #     continue

        name = extract_person_name(message_text)
        location = extract_location(message_text)
        sentiment = analyze_sentiment(message_text)
        
        if user_id not in user_data:
            user_data[user_id] = {"names": set(), "locations": set(), "sentiments": []}
        if name:
            user_data[user_id]["names"].add(name)
        if location:
            user_data[user_id]["locations"].add(location)
        user_data[user_id]["sentiments"].append(sentiment)
    
    for user_id, data in user_data.items():
        current = get_user(user_id)  # Returns (username, display_name, location, profile_info, emotional_state)
        manual_name = current[1] if current and current[1] else None
        manual_location = current[2] if current and current[2] else None

        final_name = manual_name if manual_name else (", ".join(data["names"]) if data["names"] else "Not specified")
        final_location = manual_location if manual_location else (", ".join(data["locations"]) if data["locations"] else "Not specified")
        
        # Calculate overall sentiment based on dynamic analysis.
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for s in data["sentiments"]:
            sentiment_counts[s] += 1
        overall_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        
        new_profile_info = (
            f"Names mentioned: {final_name}. "
            f"Locations: {final_location}. "
            f"Overall sentiment: {overall_sentiment}."
        )
        update_user_profile(user_id, profile_info=new_profile_info, emotional_state=overall_sentiment)
        console.log(f"[bold green]Updated user {user_id} profile:[/bold green] {new_profile_info}")
    
    cur.close()
    conn.close()

def start_scheduler():
    console.log("[bold blue]Starting background scheduler...[/bold blue]")
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(summarize_conversations, 'interval', seconds=10)
    scheduler.add_job(analyze_and_learn, 'interval', seconds=10)
    scheduler.start()
    console.log("[bold blue]Background scheduler started.[/bold blue]")
