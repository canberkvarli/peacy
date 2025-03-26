from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import psycopg2
from config import config
from rich.console import Console

# Import text analysis functions from memory_manager.
from text_analysis import extract_person_name, extract_location, analyze_sentiment
# Import update_user_profile from db_manager.
from db_manager import update_user_profile

console = Console()

def summarize_conversations():
    console.log("[bold blue]Starting summarization of conversations...[/bold blue]")
    conn = psycopg2.connect(config.PG_CONNECTION_STRING)
    cur = conn.cursor()
    # Retrieve messages from the past hour, grouped by chat.
    cur.execute("""
        SELECT chat_id, array_agg(message_text ORDER BY timestamp) as messages
        FROM messages
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        GROUP BY chat_id
    """)
    rows = cur.fetchall()
    for row in rows:
        chat_id, messages = row
        # For demonstration, simply join messages into a summary.
        summary = " ".join(messages)
        console.log(f"[bold green]Chat {chat_id} summary:[/bold green] {summary[:100]}...")
    cur.close()
    conn.close()

def analyze_and_learn():
    """
    Extract key personal details from recent messages and update user profiles.
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
        names = ", ".join(data["names"]) if data["names"] else "Not specified"
        locations = ", ".join(data["locations"]) if data["locations"] else "Not specified"
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for s in data["sentiments"]:
            sentiment_counts[s] += 1
        predominant_sentiment = max(sentiment_counts, key=sentiment_counts.get)
        profile_info = f"Names mentioned: {names}. Locations: {locations}. Overall sentiment: {predominant_sentiment}."
        update_user_profile(user_id, username="", profile_info=profile_info)
        console.log(f"[bold green]Updated user {user_id} profile:[/bold green] {profile_info}")
    
    cur.close()
    conn.close()

def start_scheduler():
    console.log("[bold blue]Starting background scheduler...[/bold blue]")
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(summarize_conversations, 'interval', seconds=10)
    scheduler.add_job(analyze_and_learn, 'interval', seconds=10)
    scheduler.start()
    console.log("[bold blue]Background scheduler started.[/bold blue]")
