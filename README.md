# ◈ stanza

**WhatsApp group chat analytics dashboard** — drop a `.txt` export and get instant insights: message leaderboards, hourly heatmaps, interaction graphs, topic breakdowns, media stats, and more.

![stanza dashboard](https://raw.githubusercontent.com/yourusername/stanza/main/screenshot.png)

---

## Features

| Section | What you get |
|---------|-------------|
| **Overview** | Total messages, unique users, ghost count, date range, daily average, peak hour, busiest weekday, media count |
| **Top Users** | Ranked leaderboard with relative activity bars |
| **Activity** | Hourly bar chart (color-coded by time of day), day-of-week chart, full daily timeline |
| **Interaction Graph** | Who replies to whom most — ranked edge list with strength bars |
| **Topics & Tech Stack** | Doughnut chart + table of topic categories; tech keyword frequency |
| **Media** | Top media senders |
| **Silent Members** | Participants who joined but never sent a message |
| **Penalties** | Detects penalty/points events mentioned in chat |

**Also:**
- 🌙 Dark / ☀️ Light theme (auto-detects system preference, persists)
- 🌐 English · Русский · Қазақша (кирилл) · Qazaqsha (latyn)
- ⬇️ Export full dashboard as standalone HTML
- 🖨️ Print / Save as PDF
- 🔒 100% local — no data leaves your machine

---

## Quick start

### Prerequisites

- Python 3.10+
- pip

### Install & run

```bash
# 1. Clone
git clone https://github.com/yourusername/stanza.git
cd stanza

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch
python web.py
```

A browser tab opens automatically at **http://127.0.0.1:5000**.

### Options

```
python web.py --help

  --host HOST       Bind host (default: 127.0.0.1)
  --port PORT       Port      (default: 5000)
  --no-browser      Don't open a browser tab automatically
```

Example — share on your local network:

```bash
python web.py --host 0.0.0.0 --port 8080
```

---

## Exporting your WhatsApp chat

1. Open the group in WhatsApp
2. Tap **⋮ → More → Export chat**
3. Choose **Without media**
4. Share / save the `.txt` file
5. Drop it into stanza

> The exported file name usually looks like `WhatsApp Chat with GroupName.txt`.  
> stanza supports both DD.MM.YYYY and DD/MM/YYYY date formats.

---

## Project structure

```
stanza/
├── web.py            ← Flask server & API routes
├── parser.py         ← WhatsApp .txt parser
├── analytics.py      ← All stat computations
├── language.py       ← i18n strings (EN / RU / KZ-C / KZ-L)
├── digest.py         ← Penalty / points event extractor
├── display.py        ← CLI display helpers
├── chat.py           ← Chat data models
├── main.py           ← CLI entry point
├── requirements.txt
├── templates/
│   └── index.html    ← Single-page dashboard (Jinja2 template)
└── static/
    ├── style.css     ← All styles (dark + light themes)
    └── app.js        ← Dashboard frontend logic
```

---

## Adding languages

Open `language.py` and add your locale key to every `_STRINGS` dict entry. Then add a button in `templates/index.html` and handle it in the `_lang_obj()` function in `web.py`.

---

## Adding topic / tech keywords

In `analytics.py`, edit the `TOPIC_KEYWORDS` or `TECH_KEYWORDS` dictionaries:

```python
TECH_KEYWORDS["Swift"] = ["swift", "swiftui", "xcode"]
TOPIC_KEYWORDS["#swift"] = ["swift", "swiftui", "ios", "xcode"]
```

---

## Requirements

```
flask>=3.0.0
```

Standard library only beyond Flask — no NumPy, pandas, or heavy dependencies.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing

Pull requests welcome. Please open an issue first for large changes.

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-thing`
3. Commit your changes
4. Open a pull request
