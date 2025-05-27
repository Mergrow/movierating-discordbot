from flask import Flask, render_template, request
import sqlite3
import math

app = Flask(__name__)
PER_PAGE = 10

@app.route("/")
def index():
    page = int(request.args.get("page", 1))
    sort = request.args.get("sort", "data")

    order_by = {
        "data": "date DESC",
        "media": "average DESC",
        "alfabetica": "movie COLLATE NOCASE ASC"
    }.get(sort, "date DESC")

    offset = (page - 1) * PER_PAGE

    conn = sqlite3.connect("ratings.db")
    c = conn.cursor()
    c.execute(f"SELECT movie, host, participants, average, date FROM ratings ORDER BY {order_by} LIMIT ? OFFSET ?", (PER_PAGE, offset))
    ratings = c.fetchall()

    c.execute("SELECT COUNT(*) FROM ratings")
    total_rows = c.fetchone()[0]
    total_pages = math.ceil(total_rows / PER_PAGE)
    conn.close()

    return render_template("index.html", ratings=ratings, page=page, total_pages=total_pages, sort=sort)
