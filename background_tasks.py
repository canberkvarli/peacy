from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import psycopg2
from config import PG_CONNECTION_STRING
from rich.console import Console

console = Console()

def summarize_conversations():
    console.log("[bold blue]Starting summarization of conversations...[/bold blue]")
    conn = psycopg2.connect(PG_CONNECTION_STRING)
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

def start_scheduler():
    console.log("[bold blue]Starting background scheduler...[/bold blue]")
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(summarize_conversations, 'interval', minutes=30)
    scheduler.start()
    console.log("[bold blue]Background scheduler started.[/bold blue]")
