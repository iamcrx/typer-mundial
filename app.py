from flask import Flask, request, redirect, url_for, render_template_string, Response
import sqlite3, os, secrets, random, csv, io, unicodedata
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "typer.db")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "potok")
TZ = ZoneInfo("Europe/Warsaw")
LONG_TERM_DEADLINE = datetime(2026, 6, 11, 21, 0, tzinfo=TZ)
AUTO_GOALS = [0, 1, 2, 3, 4]
AUTO_WEIGHTS = [25, 30, 25, 15, 5]

TEAMS = {
    "MEX": ("Meksyk", "mx"), "RSA": ("Afryka Południowa", "za"), "KOR": ("Korea Południowa", "kr"), "CZE": ("Czechy", "cz"),
    "CAN": ("Kanada", "ca"), "BIH": ("Bośnia i Hercegowina", "ba"), "USA": ("Stany Zjednoczone", "us"), "PAR": ("Paragwaj", "py"),
    "QAT": ("Katar", "qa"), "SUI": ("Szwajcaria", "ch"), "BRA": ("Brazylia", "br"), "MAR": ("Maroko", "ma"),
    "HAI": ("Haiti", "ht"), "SCO": ("Szkocja", "gb-sct"), "AUS": ("Australia", "au"), "TUR": ("Turcja", "tr"),
    "GER": ("Niemcy", "de"), "CUW": ("Curaçao", "cw"), "NED": ("Holandia", "nl"), "JPN": ("Japonia", "jp"),
    "CIV": ("Wybrzeże Kości Słoniowej", "ci"), "ECU": ("Ekwador", "ec"), "SWE": ("Szwecja", "se"), "TUN": ("Tunezja", "tn"),
    "ESP": ("Hiszpania", "es"), "CPV": ("Wyspy Zielonego Przylądka", "cv"), "BEL": ("Belgia", "be"), "EGY": ("Egipt", "eg"),
    "KSA": ("Arabia Saudyjska", "sa"), "URU": ("Urugwaj", "uy"), "IRN": ("Iran", "ir"), "NZL": ("Nowa Zelandia", "nz"),
    "FRA": ("Francja", "fr"), "SEN": ("Senegal", "sn"), "IRQ": ("Irak", "iq"), "NOR": ("Norwegia", "no"),
    "ARG": ("Argentyna", "ar"), "ALG": ("Algieria", "dz"), "AUT": ("Austria", "at"), "JOR": ("Jordania", "jo"),
    "POR": ("Portugalia", "pt"), "COD": ("DR Kongo", "cd"), "ENG": ("Anglia", "gb-eng"), "CRO": ("Chorwacja", "hr"),
    "GHA": ("Ghana", "gh"), "PAN": ("Panama", "pa"), "UZB": ("Uzbekistan", "uz"), "COL": ("Kolumbia", "co"),
}

MATCHES = [
    ("2026-06-11", "21:00", "A", "MEX", "RSA"),
    ("2026-06-12", "04:00", "A", "KOR", "CZE"), ("2026-06-12", "21:00", "B", "CAN", "BIH"),
    ("2026-06-13", "03:00", "D", "USA", "PAR"), ("2026-06-13", "21:00", "B", "QAT", "SUI"),
    ("2026-06-14", "00:00", "C", "BRA", "MAR"), ("2026-06-14", "03:00", "C", "HAI", "SCO"), ("2026-06-14", "06:00", "D", "AUS", "TUR"), ("2026-06-14", "19:00", "E", "GER", "CUW"), ("2026-06-14", "22:00", "F", "NED", "JPN"),
    ("2026-06-15", "01:00", "E", "CIV", "ECU"), ("2026-06-15", "04:00", "F", "SWE", "TUN"), ("2026-06-15", "18:00", "H", "ESP", "CPV"), ("2026-06-15", "21:00", "G", "BEL", "EGY"),
    ("2026-06-16", "00:00", "H", "KSA", "URU"), ("2026-06-16", "03:00", "I", "IRN", "NZL"), ("2026-06-16", "21:00", "I", "FRA", "SEN"),
    ("2026-06-17", "00:00", "J", "IRQ", "NOR"), ("2026-06-17", "03:00", "J", "ARG", "ALG"), ("2026-06-17", "06:00", "K", "AUT", "JOR"), ("2026-06-17", "19:00", "K", "POR", "COD"), ("2026-06-17", "22:00", "L", "ENG", "CRO"),
    ("2026-06-18", "01:00", "L", "GHA", "PAN"), ("2026-06-18", "04:00", "K", "UZB", "COL"), ("2026-06-18", "18:00", "A", "CZE", "RSA"), ("2026-06-18", "21:00", "B", "SUI", "BIH"),
    ("2026-06-19", "00:00", "B", "CAN", "QAT"), ("2026-06-19", "03:00", "A", "MEX", "KOR"), ("2026-06-19", "21:00", "D", "USA", "AUS"),
    ("2026-06-20", "00:00", "C", "SCO", "MAR"), ("2026-06-20", "02:30", "C", "BRA", "HAI"), ("2026-06-20", "05:00", "D", "TUR", "PAR"), ("2026-06-20", "19:00", "F", "NED", "SWE"), ("2026-06-20", "22:00", "E", "GER", "CIV"),
    ("2026-06-21", "02:00", "E", "ECU", "CUW"), ("2026-06-21", "08:00", "F", "TUN", "JPN"), ("2026-06-21", "18:00", "H", "ESP", "KSA"), ("2026-06-21", "21:00", "G", "BEL", "IRN"),
    ("2026-06-22", "00:00", "H", "URU", "CPV"), ("2026-06-22", "03:00", "G", "NZL", "EGY"), ("2026-06-22", "19:00", "J", "ARG", "AUT"), ("2026-06-22", "23:00", "I", "FRA", "IRQ"),
    ("2026-06-23", "01:00", "I", "NOR", "SEN"), ("2026-06-23", "05:00", "J", "JOR", "ALG"), ("2026-06-23", "19:00", "K", "POR", "UZB"), ("2026-06-23", "22:00", "L", "ENG", "GHA"),
    ("2026-06-24", "01:00", "L", "PAN", "CRO"), ("2026-06-24", "04:00", "K", "COL", "COD"), ("2026-06-24", "21:00", "B", "SUI", "CAN"), ("2026-06-24", "21:00", "B", "BIH", "QAT"),
    ("2026-06-25", "00:00", "C", "SCO", "BRA"), ("2026-06-25", "00:00", "C", "MAR", "HAI"), ("2026-06-25", "03:00", "A", "CZE", "MEX"), ("2026-06-25", "03:00", "A", "RSA", "KOR"), ("2026-06-25", "22:00", "E", "ECU", "GER"), ("2026-06-25", "22:00", "E", "CUW", "CIV"),
    ("2026-06-26", "01:00", "F", "TUN", "NED"), ("2026-06-26", "01:00", "F", "JPN", "SWE"), ("2026-06-26", "04:00", "D", "TUR", "USA"), ("2026-06-26", "04:00", "D", "PAR", "AUS"), ("2026-06-26", "21:00", "I", "NOR", "FRA"), ("2026-06-26", "21:00", "I", "SEN", "IRQ"),
    ("2026-06-27", "00:00", "H", "URU", "ESP"), ("2026-06-27", "02:00", "H", "CPV", "KSA"), ("2026-06-27", "05:00", "G", "NZL", "BEL"), ("2026-06-27", "05:00", "G", "EGY", "IRN"), ("2026-06-27", "23:00", "L", "PAN", "ENG"), ("2026-06-27", "23:00", "L", "CRO", "GHA"),
    ("2026-06-28", "01:30", "K", "COL", "POR"), ("2026-06-28", "01:30", "K", "COD", "UZB"), ("2026-06-28", "04:00", "J", "JOR", "ARG"), ("2026-06-28", "04:00", "J", "ALG", "AUT"),
]

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def column_exists(conn, table, column):
    return any(c["name"] == column for c in conn.execute(f"PRAGMA table_info({table})").fetchall())

def generate_token():
    return secrets.token_urlsafe(8).replace("-", "").replace("_", "")

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY AUTOINCREMENT, match_date TEXT, match_time TEXT, group_code TEXT, home_code TEXT, away_code TEXT, home_score INTEGER, away_score INTEGER)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS participants (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, token TEXT UNIQUE, created_at TEXT NOT NULL)""")
    if not column_exists(conn, "participants", "token"):
        cur.execute("ALTER TABLE participants ADD COLUMN token TEXT")
    cur.execute("""CREATE TABLE IF NOT EXISTS predictions (participant_id INTEGER, match_id INTEGER, home_goals INTEGER, away_goals INTEGER, points INTEGER, is_auto INTEGER DEFAULT 0, created_at TEXT, PRIMARY KEY (participant_id, match_id))""")
    if not column_exists(conn, "predictions", "is_auto"):
        cur.execute("ALTER TABLE predictions ADD COLUMN is_auto INTEGER DEFAULT 0")
    if not column_exists(conn, "predictions", "created_at"):
        cur.execute("ALTER TABLE predictions ADD COLUMN created_at TEXT")
    cur.execute("""CREATE TABLE IF NOT EXISTS long_terms (participant_id INTEGER PRIMARY KEY, champion TEXT, runner_up TEXT, third_place TEXT, golden_boot TEXT, golden_glove TEXT, points INTEGER DEFAULT 0)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")
    if cur.execute("SELECT COUNT(*) FROM matches").fetchone()[0] == 0:
        cur.executemany("INSERT INTO matches (match_date, match_time, group_code, home_code, away_code) VALUES (?, ?, ?, ?, ?)", MATCHES)
    for p in cur.execute("SELECT id FROM participants WHERE token IS NULL OR token = ''").fetchall():
        cur.execute("UPDATE participants SET token = ? WHERE id = ?", (generate_token(), p["id"]))
    conn.commit()
    conn.close()

def team_label(code):
    return TEAMS[code][0]

def flag_url(code):
    return f"https://flagcdn.com/w40/{TEAMS[code][1]}.png"

def today_iso():
    return datetime.now(TZ).date().isoformat()

def tomorrow_iso():
    return (datetime.now(TZ).date() + timedelta(days=1)).isoformat()

def base_url_for_request():
    return request.host_url.rstrip("/")

def match_datetime(row):
    y, m, d = map(int, row["match_date"].split("-"))
    hh, mm = map(int, row["match_time"].split(":"))
    return datetime(y, m, d, hh, mm, tzinfo=TZ)

def is_match_locked(row):
    return datetime.now(TZ) >= match_datetime(row)

def time_left_text(row):
    seconds = int((match_datetime(row) - datetime.now(TZ)).total_seconds())
    if seconds <= 0:
        return "zablokowane"

    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60

    if days:
        return f"{days} d {hours} godz. {minutes} min"
    if hours:
        return f"{hours} godz. {minutes} min"
    if minutes:
        return f"{minutes} min"
    return "mniej niż minuta"

def long_terms_locked():
    return datetime.now(TZ) >= LONG_TERM_DEADLINE

def normalize_text(text):
    text = unicodedata.normalize("NFKD", (text or "").strip().lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))

def get_setting(conn, key):
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else ""

def set_setting(conn, key, value):
    conn.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value or ""))

def calc_match_points(ph, pa, rh, ra):
    if ph is None or pa is None or rh is None or ra is None:
        return None
    if ph == rh and pa == ra:
        return 5
    if rh == ra:
        return 2 if ph == pa else 0

    real_winner = "H" if rh > ra else "A"
    pred_winner = "H" if ph > pa else "A" if pa > ph else "D"

    if pred_winner == real_winner:
        return 3 if (ph - pa) == (rh - ra) else 2
    return 0

def random_score():
    return (
        random.choices(AUTO_GOALS, weights=AUTO_WEIGHTS, k=1)[0],
        random.choices(AUTO_GOALS, weights=AUTO_WEIGHTS, k=1)[0],
    )

def fill_missing_auto_predictions(conn):
    participants = conn.execute("SELECT * FROM participants").fetchall()
    matches = conn.execute("SELECT * FROM matches ORDER BY match_date, match_time, id").fetchall()

    for match in matches:
        if not is_match_locked(match):
            continue

        for p in participants:
            exists = conn.execute(
                "SELECT 1 FROM predictions WHERE participant_id = ? AND match_id = ?",
                (p["id"], match["id"]),
            ).fetchone()

            if exists:
                continue

            hg, ag = random_score()
            conn.execute(
                """INSERT INTO predictions
                (participant_id, match_id, home_goals, away_goals, points, is_auto, created_at)
                VALUES (?, ?, ?, ?, NULL, 1, ?)""",
                (p["id"], match["id"], hg, ag, datetime.now(TZ).isoformat()),
            )

def recalculate_all_points():
    init_db()
    conn = connect()
    cur = conn.cursor()

    fill_missing_auto_predictions(conn)

    rows = cur.execute(
        """SELECT p.participant_id, p.match_id, p.home_goals, p.away_goals, m.home_score, m.away_score
        FROM predictions p
        JOIN matches m ON m.id = p.match_id"""
    ).fetchall()

    for r in rows:
        pts = calc_match_points(
            r["home_goals"],
            r["away_goals"],
            r["home_score"],
            r["away_score"],
        )
        cur.execute(
            "UPDATE predictions SET points = ? WHERE participant_id = ? AND match_id = ?",
            (pts, r["participant_id"], r["match_id"]),
        )

    outcomes = {
        k: get_setting(conn, k)
        for k in ["champion", "runner_up", "third_place", "golden_boot", "golden_glove"]
    }

    for lt in cur.execute("SELECT * FROM long_terms").fetchall():
        pts = 0

        if outcomes["champion"] and lt["champion"] == outcomes["champion"]:
            pts += 15
        if outcomes["runner_up"] and lt["runner_up"] == outcomes["runner_up"]:
            pts += 10
        if outcomes["third_place"] and lt["third_place"] == outcomes["third_place"]:
            pts += 10
        if normalize_text(outcomes["golden_boot"]) and normalize_text(lt["golden_boot"]) == normalize_text(outcomes["golden_boot"]):
            pts += 10
        if normalize_text(outcomes["golden_glove"]) and normalize_text(lt["golden_glove"]) == normalize_text(outcomes["golden_glove"]):
            pts += 10

        cur.execute(
            "UPDATE long_terms SET points = ? WHERE participant_id = ?",
            (pts, lt["participant_id"]),
        )

    conn.commit()
    conn.close()

def get_participant_by_token(conn, token):
    return conn.execute("SELECT * FROM participants WHERE token = ?", (token,)).fetchone()

def format_date_pl(iso_date):
    y, m, d = map(int, iso_date.split("-"))
    weekdays = ["poniedziałek", "wtorek", "środa", "czwartek", "piątek", "sobota", "niedziela"]
    dt = date(y, m, d)
    return f"{weekdays[dt.weekday()]}, {d:02d}.{m:02d}.{y}"

CSS = """
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:linear-gradient(180deg,#0f172a,#020617);color:#e5e7eb}
.container{max-width:1180px;margin:0 auto;padding:20px}
a{color:#93c5fd;text-decoration:none}
.topnav{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.topnav a{background:#1f2937;border:1px solid #374151;border-radius:999px;padding:8px 12px}
.card{background:#111827;border:1px solid #374151;border-radius:16px;padding:18px;margin-bottom:18px}
.info{color:#9ca3af;font-size:14px}
input,select,button{border-radius:10px;border:1px solid #374151;padding:10px;background:#020617;color:#e5e7eb;font-size:15px;max-width:100%}
button{cursor:pointer;background:#22c55e;color:#052e16;border:none;font-weight:bold}
.success{color:#22c55e}
.danger{color:#ef4444}
.warning{color:#facc15}
.day-title{margin-top:26px;border-left:4px solid #22c55e;padding-left:10px}
.match{display:grid;grid-template-columns:90px minmax(220px,1fr) 150px minmax(220px,1fr) 150px;gap:16px;align-items:center;padding:14px 12px;border-bottom:1px solid #374151}
.match:nth-child(even){background:rgba(31,41,55,.4)}
.team{display:flex;align-items:center;gap:12px;font-weight:bold;min-width:0}
.team-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.flag{width:30px;height:21px;object-fit:cover;border-radius:3px}
.score-box{display:flex;gap:8px;align-items:center;justify-content:center}
.score-box input{width:62px;height:42px;text-align:center}
.locked{color:#9ca3af}
.auto-badge{display:inline-block;font-size:12px;color:#111827;background:#facc15;border-radius:999px;padding:2px 8px;margin-top:4px;font-weight:bold}
.table-wrap{overflow-x:auto}
.table{width:100%;border-collapse:collapse;min-width:650px}
.table th,.table td{border-bottom:1px solid #374151;padding:10px;text-align:left;vertical-align:top}
.table th{color:#9ca3af}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.sticky-save{position:sticky;bottom:0;background:#020617;border-top:1px solid #374151;padding:16px 0;margin-top:20px}
.copy-row{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center}
.copy-input{width:100%;font-size:13px}
@media(max-width:900px){
    .container{padding:12px}
    .match{grid-template-columns:1fr}
    .score-box{justify-content:flex-start}
    .team-name{white-space:normal}
    .grid2,.copy-row{grid-template-columns:1fr}
}
</style>
<script>
function copyText(id){
    const el=document.getElementById(id);
    el.select();
    el.setSelectionRange(0,99999);
    navigator.clipboard.writeText(el.value);
}
</script>
"""

BASE = """
<!doctype html>
<html lang="pl">
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    {{ css|safe }}
</head>
<body>
    <div class="container">{{ body|safe }}</div>
</body>
</html>
"""

def render_page(title, body, **ctx):
    return render_template_string(
        BASE,
        title=title,
        css=CSS,
        body=render_template_string(body, **ctx),
    )

PLAYER_BODY = """
<div class="topnav">
    <a href="{{ url_for('player', token=participant.token) }}">Mój typer</a>
    <a href="{{ url_for('ranking') }}">Ranking</a>
    <a href="{{ url_for('picks') }}">Typy po starcie</a>
    <a href="{{ url_for('admin', key='potok') }}">Admin</a>
</div>

<h1>Typer Mundialu 2026</h1>

<div class="card">
    <h2>{{ participant.name }}</h2>
    <p class="info">
        To jest Twój indywidualny link. Jeśli nie zdążysz wytypować meczu,
        po jego rozpoczęciu system wpisze realistyczny losowy typ.
    </p>
</div>

{% if saved %}
<div class="card success">Zapisano typy.</div>
{% endif %}

<div class="card">
    <h2>Widok</h2>
    <div class="topnav">
        <a href="{{ url_for('player', token=participant.token, view='all') }}">Wszystkie</a>
        <a href="{{ url_for('player', token=participant.token, view='today') }}">Dzisiaj</a>
        <a href="{{ url_for('player', token=participant.token, view='tomorrow') }}">Jutro</a>
        <a href="{{ url_for('player', token=participant.token, view='missing') }}">Moje niewypełnione</a>
    </div>
    <p class="info">Aktualnie: <strong>{{ view_label }}</strong></p>
</div>

<div class="card">
    <h2>Zasady punktacji</h2>
    <p class="info">
        5 pkt – dokładny wynik. 3 pkt – zwycięzca i trafiona różnica bramek.
        2 pkt – trafiony zwycięzca albo remis. Przy remisach nie ma premii za różnicę bramek.
    </p>
</div>

<form method="post">
    <div class="card">
        <h2>Typy długoterminowe</h2>

        {% if long_locked %}
        <p class="danger">Typy długoterminowe są już zablokowane.</p>
        {% else %}
        <p class="info">Typy długoterminowe można edytować do {{ long_deadline }}.</p>
        {% endif %}

        <div class="grid2">
            <label>
                Mistrz świata – 15 pkt<br>
                <select name="champion" {% if long_locked %}disabled{% endif %}>
                    <option value="">-- wybierz --</option>
                    {% for code,label in team_options %}
                    <option value="{{ code }}" {% if long_term.champion == code %}selected{% endif %}>{{ label }}</option>
                    {% endfor %}
                </select>
            </label>

            <label>
                Wicemistrz świata – 10 pkt<br>
                <select name="runner_up" {% if long_locked %}disabled{% endif %}>
                    <option value="">-- wybierz --</option>
                    {% for code,label in team_options %}
                    <option value="{{ code }}" {% if long_term.runner_up == code %}selected{% endif %}>{{ label }}</option>
                    {% endfor %}
                </select>
            </label>

            <label>
                3. miejsce – 10 pkt<br>
                <select name="third_place" {% if long_locked %}disabled{% endif %}>
                    <option value="">-- wybierz --</option>
                    {% for code,label in team_options %}
                    <option value="{{ code }}" {% if long_term.third_place == code %}selected{% endif %}>{{ label }}</option>
                    {% endfor %}
                </select>
            </label>

            <label>
                Król strzelców – 10 pkt<br>
                <input name="golden_boot" value="{{ long_term.golden_boot or '' }}" {% if long_locked %}disabled{% endif %}>
            </label>

            <label>
                Złota rękawica – 10 pkt<br>
                <input name="golden_glove" value="{{ long_term.golden_glove or '' }}" {% if long_locked %}disabled{% endif %}>
            </label>
        </div>
    </div>

    <div class="card">
        <h2>Mecze fazy grupowej</h2>

        {% if not grouped_matches %}
        <p class="warning">Brak meczów w tym widoku.</p>
        {% endif %}

        {% for day, ms in grouped_matches.items() %}
        <h3 class="day-title">{{ format_date_pl(day) }}</h3>

        {% for match in ms %}
        {% set pred = predictions.get(match.id) %}

        <div class="match">
            <div>
                {{ match.match_time }}<br>
                <span class="info">gr. {{ match.group_code }}</span>
            </div>

            <div class="team">
                <img class="flag" src="{{ flag_url(match.home_code) }}">
                <span class="team-name">{{ teams[match.home_code][0] }}</span>
            </div>

            <div class="score-box">
                <input type="number" min="0" max="30" name="home_{{ match.id }}" value="{{ pred.home_goals if pred else '' }}" {% if match.locked %}disabled{% endif %}>
                :
                <input type="number" min="0" max="30" name="away_{{ match.id }}" value="{{ pred.away_goals if pred else '' }}" {% if match.locked %}disabled{% endif %}>
            </div>

            <div class="team">
                <img class="flag" src="{{ flag_url(match.away_code) }}">
                <span class="team-name">{{ teams[match.away_code][0] }}</span>
            </div>

            <div>
                {% if match.home_score is not none and match.away_score is not none %}
                wynik: {{ match.home_score }}:{{ match.away_score }}<br>
                {% endif %}

                {% if pred and pred.points is not none %}
                <strong>{{ pred.points }} pkt</strong><br>
                {% elif match.locked %}
                <span class="locked">zablokowane</span><br>
                {% else %}
                <span class="success">pozostało: {{ match.time_left }}</span><br>
                {% endif %}

                {% if pred and pred.is_auto %}
                <span class="auto-badge">AUTO</span>
                {% endif %}
            </div>
        </div>
        {% endfor %}
        {% endfor %}
    </div>

    <div class="sticky-save">
        <button type="submit">Zapisz typy</button>
    </div>
</form>
"""

@app.route("/")
def index():
    init_db()
    body = """
    <div class="topnav">
        <a href="{{ url_for('ranking') }}">Ranking</a>
        <a href="{{ url_for('picks') }}">Typy po starcie</a>
        <a href="{{ url_for('admin', key='potok') }}">Admin</a>
    </div>

    <h1>Typer Mundialu 2026</h1>

    <div class="card">
        <h2>Wejście do gry</h2>
        <p>Każdy uczestnik powinien dostać indywidualny link z panelu admina.</p>
        <p><a href="{{ url_for('admin', key='potok') }}">Przejdź do panelu admina</a></p>
    </div>
    """
    return render_page("Typer Mundialu", body)

@app.route("/player/<token>", methods=["GET", "POST"])
def player(token):
    init_db()
    recalculate_all_points()

    conn = connect()
    participant = get_participant_by_token(conn, token)

    if not participant:
        conn.close()
        return "Nie znaleziono uczestnika.", 404

    if request.method == "POST":
        pid = participant["id"]

        if not long_terms_locked():
            conn.execute(
                """INSERT INTO long_terms
                (participant_id, champion, runner_up, third_place, golden_boot, golden_glove)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(participant_id) DO UPDATE SET
                    champion=excluded.champion,
                    runner_up=excluded.runner_up,
                    third_place=excluded.third_place,
                    golden_boot=excluded.golden_boot,
                    golden_glove=excluded.golden_glove""",
                (
                    pid,
                    request.form.get("champion", ""),
                    request.form.get("runner_up", ""),
                    request.form.get("third_place", ""),
                    request.form.get("golden_boot", "").strip(),
                    request.form.get("golden_glove", "").strip(),
                ),
            )

        for m in conn.execute("SELECT * FROM matches ORDER BY match_date, match_time, id").fetchall():
            if is_match_locked(m):
                continue

            hr = request.form.get(f"home_{m['id']}", "").strip()
            ar = request.form.get(f"away_{m['id']}", "").strip()

            if hr == "" or ar == "":
                continue

            try:
                hg, ag = int(hr), int(ar)
            except ValueError:
                continue

            if hg < 0 or ag < 0:
                continue

            conn.execute(
                """INSERT INTO predictions
                (participant_id, match_id, home_goals, away_goals, points, is_auto, created_at)
                VALUES (?, ?, ?, ?, NULL, 0, ?)
                ON CONFLICT(participant_id, match_id) DO UPDATE SET
                    home_goals=excluded.home_goals,
                    away_goals=excluded.away_goals,
                    is_auto=0,
                    created_at=excluded.created_at""",
                (pid, m["id"], hg, ag, datetime.now(TZ).isoformat()),
            )

        conn.commit()
        conn.close()
        recalculate_all_points()

        return redirect(url_for("player", token=token, saved="1", view=request.args.get("view", "all")))

    lt = conn.execute("SELECT * FROM long_terms WHERE participant_id = ?", (participant["id"],)).fetchone()
    long_term = dict(lt) if lt else {
        "champion": "",
        "runner_up": "",
        "third_place": "",
        "golden_boot": "",
        "golden_glove": "",
    }

    pred_rows = conn.execute(
        "SELECT * FROM predictions WHERE participant_id = ?",
        (participant["id"],),
    ).fetchall()

    predictions = {r["match_id"]: r for r in pred_rows}
    matches = conn.execute("SELECT * FROM matches ORDER BY match_date, match_time, id").fetchall()
    conn.close()

    view = request.args.get("view", "all")
    prepared = []

    for r in matches:
        rd = dict(r)
        rd["locked"] = is_match_locked(r)
        rd["time_left"] = time_left_text(r)
        pred = predictions.get(r["id"])

        if view == "today" and r["match_date"] != today_iso():
            continue
        if view == "tomorrow" and r["match_date"] != tomorrow_iso():
            continue
        if view == "missing" and (pred or rd["locked"]):
            continue

        prepared.append(rd)

    grouped = {}

    for r in prepared:
        grouped.setdefault(r["match_date"], []).append(r)

    team_options = sorted([(c, team_label(c)) for c in TEAMS], key=lambda x: x[1])

    labels = {
        "all": "wszystkie mecze",
        "today": "dzisiejsze mecze",
        "tomorrow": "jutrzejsze mecze",
        "missing": "moje niewypełnione typy",
    }

    return render_page(
        "Typer",
        PLAYER_BODY,
        participant=participant,
        saved=request.args.get("saved") == "1",
        teams=TEAMS,
        flag_url=flag_url,
        grouped_matches=grouped,
        predictions=predictions,
        long_term=long_term,
        long_locked=long_terms_locked(),
        long_deadline=LONG_TERM_DEADLINE.strftime("%d.%m.%Y, %H:%M"),
        team_options=team_options,
        format_date_pl=format_date_pl,
        view_label=labels.get(view, "wszystkie mecze"),
    )

@app.route("/ranking")
def ranking():
    init_db()
    recalculate_all_points()

    conn = connect()

    rows = conn.execute(
        """SELECT
            p.name,
            p.token,
            COALESCE(SUM(pr.points),0) match_points,
            COALESCE(lt.points,0) long_points,
            COALESCE(SUM(pr.points),0)+COALESCE(lt.points,0) total_points
        FROM participants p
        LEFT JOIN predictions pr ON pr.participant_id=p.id
        LEFT JOIN long_terms lt ON lt.participant_id=p.id
        GROUP BY p.id
        ORDER BY total_points DESC, match_points DESC, p.name ASC"""
    ).fetchall()

    conn.close()

    body = """
    <div class="topnav">
        <a href="{{ url_for('index') }}">Start</a>
        <a href="{{ url_for('picks') }}">Typy po starcie</a>
        <a href="{{ url_for('admin', key='potok') }}">Admin</a>
    </div>

    <h1>Ranking</h1>

    <div class="card table-wrap">
        <table class="table">
            <tr>
                <th>Miejsce</th>
                <th>Uczestnik</th>
                <th>Mecze</th>
                <th>Długoterminowe</th>
                <th>Razem</th>
                <th>Szczegóły</th>
            </tr>

            {% for r in rows %}
            <tr>
                <td>{{ loop.index }}</td>
                <td><strong>{{ r.name }}</strong></td>
                <td>{{ r.match_points }}</td>
                <td>{{ r.long_points }}</td>
                <td><strong>{{ r.total_points }}</strong></td>
                <td><a href="{{ url_for('player_details', token=r.token) }}">pokaż</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    """

    return render_page("Ranking", body, rows=rows)

@app.route("/ranking/player/<token>")
def player_details(token):
    init_db()
    recalculate_all_points()

    conn = connect()
    p = get_participant_by_token(conn, token)

    if not p:
        conn.close()
        return "Nie znaleziono uczestnika.", 404

    rows = conn.execute(
        """SELECT
            m.*,
            pr.home_goals,
            pr.away_goals,
            pr.points,
            pr.is_auto
        FROM matches m
        LEFT JOIN predictions pr ON pr.match_id=m.id AND pr.participant_id=?
        ORDER BY m.match_date, m.match_time, m.id""",
        (p["id"],),
    ).fetchall()

    conn.close()

    body = """
    <div class="topnav">
        <a href="{{ url_for('ranking') }}">Ranking</a>
        <a href="{{ url_for('picks') }}">Typy po starcie</a>
    </div>

    <h1>Szczegóły: {{ p.name }}</h1>

    <div class="card table-wrap">
        <table class="table">
            <tr>
                <th>Data</th>
                <th>Mecz</th>
                <th>Typ</th>
                <th>Wynik</th>
                <th>Punkty</th>
            </tr>

            {% for r in rows %}
            <tr>
                <td>{{ r.match_date }} {{ r.match_time }}</td>
                <td>{{ teams[r.home_code][0] }} – {{ teams[r.away_code][0] }}</td>
                <td>
                    {% if r.home_goals is not none %}
                    {{ r.home_goals }}:{{ r.away_goals }}
                    {% if r.is_auto %}<span class="auto-badge">AUTO</span>{% endif %}
                    {% else %}
                    -
                    {% endif %}
                </td>
                <td>
                    {% if r.home_score is not none %}
                    {{ r.home_score }}:{{ r.away_score }}
                    {% else %}
                    -
                    {% endif %}
                </td>
                <td>{{ r.points if r.points is not none else '-' }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    """

    return render_page("Szczegóły", body, p=p, rows=rows, teams=TEAMS)

@app.route("/picks")
def picks():
    init_db()
    recalculate_all_points()

    conn = connect()
    matches = []
    picks_by_match = {}

    for m in conn.execute("SELECT * FROM matches ORDER BY match_date, match_time, id").fetchall():
        md = dict(m)
        md["locked"] = is_match_locked(m)
        matches.append(md)

        if md["locked"]:
            picks_by_match[m["id"]] = conn.execute(
                """SELECT
                    p.name,
                    pr.home_goals,
                    pr.away_goals,
                    pr.points,
                    pr.is_auto
                FROM participants p
                JOIN predictions pr ON pr.participant_id=p.id
                WHERE pr.match_id=?
                ORDER BY p.name""",
                (m["id"],),
            ).fetchall()
        else:
            picks_by_match[m["id"]] = []

    conn.close()

    body = """
    <div class="topnav">
        <a href="{{ url_for('index') }}">Start</a>
        <a href="{{ url_for('ranking') }}">Ranking</a>
        <a href="{{ url_for('admin', key='potok') }}">Admin</a>
    </div>

    <h1>Typy wszystkich graczy</h1>

    <div class="card">
        <p class="info">Typy danego meczu są widoczne dopiero po rozpoczęciu tego meczu.</p>
    </div>

    {% for m in matches %}
    <div class="card">
        <h2>{{ m.match_date }} {{ m.match_time }} — {{ teams[m.home_code][0] }} – {{ teams[m.away_code][0] }}</h2>

        {% if not m.locked %}
        <p class="warning">Typy ukryte do rozpoczęcia meczu.</p>
        {% else %}
        <div class="table-wrap">
            <table class="table">
                <tr>
                    <th>Uczestnik</th>
                    <th>Typ</th>
                    <th>Wynik</th>
                    <th>Punkty</th>
                </tr>

                {% for p in picks_by_match[m.id] %}
                <tr>
                    <td>{{ p.name }}</td>
                    <td>
                        {{ p.home_goals }}:{{ p.away_goals }}
                        {% if p.is_auto %}<span class="auto-badge">AUTO</span>{% endif %}
                    </td>
                    <td>
                        {% if m.home_score is not none %}
                        {{ m.home_score }}:{{ m.away_score }}
                        {% else %}
                        -
                        {% endif %}
                    </td>
                    <td>{{ p.points if p.points is not none else '-' }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
        {% endif %}
    </div>
    {% endfor %}
    """

    return render_page("Typy", body, matches=matches, picks_by_match=picks_by_match, teams=TEAMS)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    init_db()

    key = request.args.get("key") or request.form.get("key") or ""

    if key != ADMIN_KEY:
        return "Brak dostępu. Użyj adresu /admin?key=potok", 403

    conn = connect()
    saved = False

    if request.method == "POST":
        for k in ["champion", "runner_up", "third_place", "golden_boot", "golden_glove"]:
            set_setting(conn, k, request.form.get(k, "").strip())

        for m in conn.execute("SELECT * FROM matches ORDER BY match_date, match_time, id").fetchall():
            hr = request.form.get(f"real_home_{m['id']}", "").strip()
            ar = request.form.get(f"real_away_{m['id']}", "").strip()

            if hr == "" or ar == "":
                conn.execute("UPDATE matches SET home_score=NULL, away_score=NULL WHERE id=?", (m["id"],))
                continue

            try:
                hs, aas = int(hr), int(ar)
            except ValueError:
                continue

            conn.execute("UPDATE matches SET home_score=?, away_score=? WHERE id=?", (hs, aas, m["id"]))

        conn.commit()
        saved = True

    settings = {
        k: get_setting(conn, k)
        for k in ["champion", "runner_up", "third_place", "golden_boot", "golden_glove"]
    }

    matches = conn.execute("SELECT * FROM matches ORDER BY match_date, match_time, id").fetchall()
    participants = conn.execute("SELECT * FROM participants ORDER BY name").fetchall()
    conn.close()

    recalculate_all_points()

    team_options = sorted([(c, team_label(c)) for c in TEAMS], key=lambda x: x[1])

    body = """
    <div class="topnav">
        <a href="{{ url_for('index') }}">Start</a>
        <a href="{{ url_for('ranking') }}">Ranking</a>
        <a href="{{ url_for('picks') }}">Typy po starcie</a>
        <a href="{{ url_for('export_csv', key=key) }}">Eksport CSV</a>
    </div>

    <h1>Panel admina</h1>

    {% if saved %}
    <div class="card success">Zapisano zmiany i przeliczono punkty.</div>
    {% endif %}

    <div class="card">
        <h2>Dodaj uczestnika</h2>
        <form method="post" action="{{ url_for('add_participant') }}">
            <input type="hidden" name="key" value="{{ key }}">
            <input name="name" placeholder="Imię uczestnika" required>
            <button>Dodaj</button>
        </form>
    </div>

    <div class="card">
        <h2>Uczestnicy i linki</h2>

        {% for p in participants %}
        <div style="margin-bottom:14px">
            <strong>{{ p.name }}</strong>
            <div class="copy-row">
                <input class="copy-input" id="link_{{ p.id }}" readonly value="{{ base_url }}/player/{{ p.token }}">
                <button type="button" onclick="copyText('link_{{ p.id }}')">Kopiuj link</button>
            </div>
        </div>
        {% endfor %}
    </div>

    <form method="post">
        <input type="hidden" name="key" value="{{ key }}">

        <div class="card">
            <h2>Końcowe rozstrzygnięcia turnieju</h2>

            <div class="grid2">
                {% for field,label in [('champion','Mistrz świata'),('runner_up','Wicemistrz świata'),('third_place','3. miejsce')] %}
                <label>
                    {{ label }}<br>
                    <select name="{{ field }}">
                        <option value="">-- brak --</option>
                        {% for code,tlabel in team_options %}
                        <option value="{{ code }}" {% if settings[field] == code %}selected{% endif %}>{{ tlabel }}</option>
                        {% endfor %}
                    </select>
                </label>
                {% endfor %}

                <label>
                    Król strzelców<br>
                    <input name="golden_boot" value="{{ settings.golden_boot }}">
                </label>

                <label>
                    Złota rękawica<br>
                    <input name="golden_glove" value="{{ settings.golden_glove }}">
                </label>
            </div>
        </div>

        <div class="card">
            <h2>Wyniki meczów</h2>

            {% for m in matches %}
            <div class="match">
                <div>
                    {{ m.match_date }}<br>
                    {{ m.match_time }}<br>
                    <span class="info">gr. {{ m.group_code }}</span>
                </div>

                <div class="team">
                    <img class="flag" src="{{ flag_url(m.home_code) }}">
                    <span class="team-name">{{ teams[m.home_code][0] }}</span>
                </div>

                <div class="score-box">
                    <input type="number" min="0" max="30" name="real_home_{{ m.id }}" value="{{ m.home_score if m.home_score is not none else '' }}">
                    :
                    <input type="number" min="0" max="30" name="real_away_{{ m.id }}" value="{{ m.away_score if m.away_score is not none else '' }}">
                </div>

                <div class="team">
                    <img class="flag" src="{{ flag_url(m.away_code) }}">
                    <span class="team-name">{{ teams[m.away_code][0] }}</span>
                </div>

                <div></div>
            </div>
            {% endfor %}
        </div>

        <div class="sticky-save">
            <button>Zapisz wyniki i przelicz punkty</button>
        </div>
    </form>
    """

    return render_page(
        "Admin",
        body,
        key=key,
        saved=saved,
        participants=participants,
        base_url=base_url_for_request(),
        settings=settings,
        team_options=team_options,
        matches=matches,
        teams=TEAMS,
        flag_url=flag_url,
    )

@app.route("/admin/add_participant", methods=["POST"])
def add_participant():
    init_db()

    key = request.form.get("key", "")

    if key != ADMIN_KEY:
        return "Brak dostępu.", 403

    name = request.form.get("name", "").strip()

    if name:
        conn = connect()
        exists = conn.execute(
            "SELECT id FROM participants WHERE lower(name)=lower(?)",
            (name,),
        ).fetchone()

        if not exists:
            conn.execute(
                "INSERT INTO participants (name, token, created_at) VALUES (?, ?, ?)",
                (name, generate_token(), datetime.now(TZ).isoformat()),
            )
            conn.commit()

        conn.close()
        recalculate_all_points()

    return redirect(url_for("admin", key=key))

@app.route("/admin/export.csv")
def export_csv():
    init_db()
    recalculate_all_points()

    key = request.args.get("key", "")

    if key != ADMIN_KEY:
        return "Brak dostępu.", 403

    conn = connect()

    rows = conn.execute(
        """SELECT
            p.name participant,
            m.match_date,
            m.match_time,
            m.group_code,
            m.home_code,
            m.away_code,
            pr.home_goals,
            pr.away_goals,
            m.home_score,
            m.away_score,
            pr.points,
            pr.is_auto
        FROM participants p
        CROSS JOIN matches m
        LEFT JOIN predictions pr ON pr.participant_id=p.id AND pr.match_id=m.id
        ORDER BY p.name, m.match_date, m.match_time, m.id"""
    ).fetchall()

    conn.close()

    out = io.StringIO()
    writer = csv.writer(out, delimiter=";")

    writer.writerow([
        "uczestnik",
        "data",
        "godzina",
        "grupa",
        "gospodarz",
        "gosc",
        "typ_gospodarz",
        "typ_gosc",
        "wynik_gospodarz",
        "wynik_gosc",
        "punkty",
        "auto",
    ])

    for r in rows:
        writer.writerow([
            r["participant"],
            r["match_date"],
            r["match_time"],
            r["group_code"],
            TEAMS[r["home_code"]][0],
            TEAMS[r["away_code"]][0],
            r["home_goals"] if r["home_goals"] is not None else "",
            r["away_goals"] if r["away_goals"] is not None else "",
            r["home_score"] if r["home_score"] is not None else "",
            r["away_score"] if r["away_score"] is not None else "",
            r["points"] if r["points"] is not None else "",
            "TAK" if r["is_auto"] else "NIE",
        ])

    return Response(
        out.getvalue().encode("utf-8-sig"),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=typer_mundial_export.csv"},
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)