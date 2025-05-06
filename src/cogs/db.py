import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo  # Requer Python 3.9+
 
DB_PATH = "ratings.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie TEXT NOT NULL,
            host TEXT NOT NULL,
            participants TEXT NOT NULL,
            average REAL NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_rating(movie: str, votes: dict, host_name: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    participants_str = "; ".join([f"{user} = {score}" for user, score in votes.values()])
    average = sum(score for (_, score) in votes.values()) / len(votes)
    
    # Get current time in Brazil (São Paulo timezone)
    br_time = datetime.now(ZoneInfo("America/Sao_Paulo"))
    date_str = br_time.strftime("%Y-%m-%d %H:%M:%S")

    c.execute("""
        INSERT INTO ratings (movie, host, participants, average, date)
        VALUES (?, ?, ?, ?, ?)
    """, (movie, host_name, participants_str, average, date_str))

    conn.commit()
    conn.close()
