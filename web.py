"""
stanza - web interface
Flask server that exposes analytics data as JSON endpoints
and serves the single-page dashboard.
Usage:
    python web.py
    python web.py --host 0.0.0.0 --port 8080 --no-browser
"""
from __future__ import annotations
import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path
from flask import Flask, jsonify, render_template, request
sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_file, Message
import analytics as an
from language import T, EN, RU, KZ_C, KZ_L
BASE_DIR = Path(__file__).parent
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)
_messages: list[Message] = []
_chat_path: str = ""
def _loaded() -> bool:
    return len(_messages) > 0
def _lang_obj(lang: str):
    return {EN: EN, RU: RU, "kz_c": KZ_C, "kz_l": KZ_L}.get(lang.lower(), EN)
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/api/upload", methods=["POST"])
def upload():
    global _messages, _chat_path
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename"}), 400
    if not f.filename.endswith(".txt"):
        return jsonify({"error": "Only .txt WhatsApp exports are supported"}), 400
    dest = BASE_DIR / "uploaded_chat.txt"
    f.save(str(dest))
    try:
        _messages = parse_file(dest)
        _chat_path = f.filename
    except Exception as e:
        return jsonify({"error": f"Parse error: {e}"}), 500
    um = an.user_messages(_messages)
    return jsonify({
        "ok": True,
        "filename": f.filename,
        "total": len(_messages),
        "user_messages": len(um),
        "system_messages": len(_messages) - len(um),
    })
@app.route("/api/strings")
def strings():
    lang = request.args.get("lang", "en")
    T.set_lang(_lang_obj(lang))
    keys = [
        "app_subtitle", "nav_overview", "nav_users", "nav_activity",
        "nav_graph", "nav_topics", "nav_media", "nav_ghosts", "nav_penalties",
        "section_summary", "section_users", "section_activity", "section_graph",
        "section_topics", "section_media", "section_ghosts", "section_penalties",
        "summary_messages", "summary_user", "summary_system",
        "summary_unique_users", "summary_ghosts_note", "summary_date_range",
        "summary_days", "summary_avg_day", "summary_peak_hour",
        "summary_active_day", "summary_media",
        "col_rank", "col_user", "col_messages", "col_activity",
        "col_day", "col_date", "col_hour", "col_count", "col_replied",
        "col_to", "col_times", "col_strength", "col_identifier",
        "col_time", "col_issuer", "col_points", "col_message",
        "col_tech", "col_mentions", "col_tag", "col_share",
        "no_data", "no_interactions", "no_ghosts", "no_penalties",
        "no_media", "no_tech", "no_topics",
        "title_hourly", "title_weekday", "title_daily",
        "time_night", "time_morning", "time_afternoon", "time_evening",
        "interaction_note",
        "upload_prompt", "upload_button", "upload_hint",
        "export_html", "export_pdf", "theme_toggle",
        "loading", "analyzing", "chat_file",
        "lang_en", "lang_ru", "lang_kz", "lang_kz_cyrillic", "lang_kz_latin",
    ]
    result = {}
    for k in keys:
        try:
            result[k] = T(k)
        except Exception:
            result[k] = k
    result["weekday_names"] = T.weekday_names()
    return jsonify(result)
@app.route("/api/summary")
def summary():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    lang = request.args.get("lang", "en")
    T.set_lang(_lang_obj(lang))
    stats = an.compute_stats(_messages)
    start, end = stats.date_range
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    active_day = (
        T.weekday_names()[weekdays.index(stats.most_active_day)]
        if stats.most_active_day in weekdays
        else stats.most_active_day
    )
    return jsonify({
        "total_messages":   stats.total_messages,
        "user_messages":    stats.user_messages,
        "system_messages":  stats.system_messages,
        "unique_users":     stats.unique_users,
        "ghost_count":      stats.ghost_count,
        "date_start":       start.strftime("%d %b %Y"),
        "date_end":         end.strftime("%d %b %Y"),
        "duration_days":    (end - start).days + 1,
        "avg_per_day":      stats.avg_messages_per_day,
        "peak_hour":        stats.most_active_hour,
        "most_active_day":  active_day,
        "total_media":      stats.total_media,
    })
@app.route("/api/users")
def users():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    n = int(request.args.get("n", 25))
    data = an.top_users(_messages, n=n)
    return jsonify([{"user": u, "count": c} for u, c in data])
@app.route("/api/activity")
def activity():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    lang = request.args.get("lang", "en")
    T.set_lang(_lang_obj(lang))
    by_hour    = an.activity_by_hour(_messages)
    by_weekday = an.activity_by_weekday(_messages)
    by_date    = an.activity_by_date(_messages)
    wnames     = T.weekday_names()
    return jsonify({
        "hourly":  [{"hour": h, "label": f"{h:02d}:00", "count": by_hour.get(h, 0)} for h in range(24)],
        "weekday": [{"day": d, "label": wnames[d], "count": by_weekday.get(d, 0)} for d in range(7)],
        "daily":   [{"date": str(d), "label": d.strftime("%d %b"), "count": c} for d, c in by_date.items()],
    })
@app.route("/api/graph")
def graph():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    n      = int(request.args.get("n", 20))
    window = int(request.args.get("window", 120))
    edges  = an.top_interactions(_messages, n=n, window_seconds=window)
    return jsonify([{"source": e.source, "target": e.target, "weight": e.weight} for e in edges])
@app.route("/api/topics")
def topics():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    dist  = an.topic_distribution(_messages)
    total = sum(dist.values())
    return jsonify([
        {"tag": tag, "count": count, "pct": round(count / total * 100, 1) if total else 0}
        for tag, count in sorted(dist.items(), key=lambda x: x[1], reverse=True)
    ])
@app.route("/api/tech")
def tech():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    data = an.extract_tech_stack(_messages)
    return jsonify([{"tech": t, "count": c} for t, c in data])
@app.route("/api/media")
def media():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    n    = int(request.args.get("n", 20))
    data = an.media_by_user(_messages)[:n]
    return jsonify([{"user": u, "count": c} for u, c in data])
@app.route("/api/ghosts")
def ghosts():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    return jsonify(an.ghost_participants(_messages))
@app.route("/api/penalties")
def penalties():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    evs = an.extract_penalties(_messages)
    return jsonify([
        {"dt": e.dt, "issuer": e.issuer, "amount": e.amount, "text": e.raw_text}
        for e in evs
    ])
@app.route("/api/export/html")
def export_html():
    if not _loaded():
        return jsonify({"error": "No chat loaded"}), 400
    return jsonify({"ok": True, "method": "client"})
def run(host: str = "127.0.0.1", port: int = 5000, open_browser: bool = True):
    if open_browser:
        def _open():
            import time
            time.sleep(0.9)
            webbrowser.open(f"http://{host}:{port}")
        threading.Thread(target=_open, daemon=True).start()
    print(f"\n  ◈  Stanza")
    print(f"     http://{host}:{port}")
    print(f"     Ctrl+C to stop\n")
    app.run(host=host, port=port, debug=False, use_reloader=False)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stanza - WhatsApp chat dashboard")
    parser.add_argument("--host",       default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port",       default=5000, type=int, help="Port (default: 5000)")
    parser.add_argument("--no-browser", action="store_true",   help="Don't open browser automatically")
    args = parser.parse_args()
    run(host=args.host, port=args.port, open_browser=not args.no_browser)
