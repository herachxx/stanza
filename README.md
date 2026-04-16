# ◈ Stanza

> **WhatsApp group chat analytics - in your browser, fully private.**

<img width="640" height="360" alt="Web-1" src="Preview (stanza)/Web-1.png" />

Drop a `.txt` export from any WhatsApp group and get an instant, interactive dashboard: message leaderboards, hourly heatmaps, who-replies-to-whom interaction graphs, topic breakdowns, media stats, and more - all without sending your data anywhere.

---

## Table of Contents

- [What is stanza?](#what-is-stanza)
- [Features](#features)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running](#running)
  - [CLI Options](#cli-options)
- [How to Export Your WhatsApp Chat](#how-to-export-your-whatsapp-chat)
- [Project Structure](#project-structure)
- [Customization](#customization)
  - [Adding Languages](#adding-languages)
  - [Adding Topic / Tech Keywords](#adding-topic--tech-keywords)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)

---

## What is stanza?

Stanza is a **local-first** analytics tool for WhatsApp group chats. You export your chat as a `.txt` file directly from WhatsApp, then stanza parses it and renders a full-featured dashboard in your browser.

**Your data never leaves your machine.** There is no backend, no cloud service, no account required.

---

## Features

| Section | What you get |
|---|---|
| **Overview** | Total messages, unique users, ghost count, date range, daily average, peak hour, busiest weekday, media count |
| **Top Users** | Ranked leaderboard with relative activity bars |
| **Activity** | Hourly bar chart (color-coded by time of day), day-of-week chart, full daily timeline |
| **Interaction Graph** | Who replies to whom most — ranked edge list with strength bars |
| **Topics & Tech Stack** | Doughnut chart + table of topic categories; tech keyword frequency |
| **Media** | Top media senders |
| **Silent Members** | Participants who joined but never sent a message |
| **Penalties** | Detects penalty/points events mentioned in chat |

**Also:**
- Dark / Light theme - auto-detects your system preference and remembers it
- Multilingual - English · Русский · Қазақша (кирилл) · Qazaqsha (latyn)
- Export the full dashboard as a **standalone HTML file** (shareable, no server needed)
- Print or save as PDF directly from the browser
- **100% local** - no data leaves your machine

---

## Quick Start

### Prerequisites

Before you begin, make sure you have the following installed:

| Tool | Minimum version | Check with |
|---|---|---|
| Python | 3.10 | `python --version` |
| pip | any recent | `pip --version` |

> **Don't have Python?** Download it from [python.org](https://www.python.org/downloads/). On Windows, check **"Add Python to PATH"** during installation.

---

### Installation

Open your terminal (Command Prompt / PowerShell on Windows, Terminal on macOS/Linux) and run these commands one by one:

```bash
# 1. Clone the repository
git clone https://github.com/herachxx/stanza.git
cd stanza
```

```bash
# 2. Create a virtual environment
#    This keeps stanza's dependencies isolated from your system Python.
python -m venv .venv
```

```bash
# 3. Activate the virtual environment
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows (Command Prompt)
# .venv\Scripts\Activate.ps1     # Windows (PowerShell)
```

> After activation you should see `(.venv)` at the start of your terminal prompt.

```bash
# 4. Install dependencies
pip install -r requirements.txt
```

---

### Running

```bash
python web.py
```

A browser tab will open automatically at **http://127.0.0.1:5000**.

From there, click **Upload** and select your WhatsApp `.txt` export file. The dashboard loads instantly.

---

### CLI Options

```
python web.py --help

  --host HOST       Bind host (default: 127.0.0.1)
  --port PORT       Port      (default: 5000)
  --no-browser      Don't open a browser tab automatically
```

**Examples:**

```bash
# Use a different port
python web.py --port 8080

# Share with other devices on your local network
python web.py --host 0.0.0.0 --port 8080
```

> (!) Using `--host 0.0.0.0` makes stanza accessible to anyone on your Wi-Fi network. Use this only on trusted networks.

---

## How to Export Your WhatsApp Chat

**On Android:**
1. Open the group chat in WhatsApp
2. Tap the **⋮** (three dots) menu in the top-right corner
3. Tap **More → Export chat**
4. Choose **Without media**
5. Save or share the `.txt` file to your computer

**On iPhone:**
1. Open the group chat in WhatsApp
2. Tap the group name at the top to open group info
3. Scroll down and tap **Export Chat**
4. Choose **Without Media**
5. Save or AirDrop the `.txt` file to your computer

The exported file is usually named something like:
`WhatsApp Chat with YourGroupName.txt`

> stanza supports both `DD.MM.YYYY` and `DD/MM/YYYY` date formats, so exports from any region should work.

---

## Project Structure

```
stanza/
│
├── web.py              ← Flask server & REST API routes (start here)
├── parser.py           ← Parses the WhatsApp .txt export into structured messages
├── analytics.py        ← All stat computations (message counts, graphs, topics…)
├── language.py         ← Internationalization strings (EN / RU / KZ-Cyrillic / KZ-Latin)
├── digest.py           ← Extracts penalty/points events from chat messages
├── display.py          ← CLI display helpers (rich/prettytable formatting)
├── chat.py             ← Chat data models (Message dataclass and related types)
├── main.py             ← CLI entry point (alternative to the web interface)
│
├── requirements.txt    ← Python dependencies
│
├── templates/
│   └── index.html      ← Single-page dashboard (Jinja2 template)
│
└── static/
    ├── style.css       ← All styles, including dark and light themes
    └── app.js          ← Dashboard frontend logic (charts, upload, language switching)
```

**New to the codebase?** A good reading order is:
`parser.py` → `chat.py` → `analytics.py` → `web.py` → `templates/index.html`

---

## Customization

### Adding Languages

1. Open `language.py`
2. Add your locale key to **every** entry in the `_STRINGS` dictionary
3. Add a language button in `templates/index.html`
4. Register the new locale in the `_lang_obj()` function inside `web.py`

### Adding Topic / Tech Keywords

Open `analytics.py` and edit the `TOPIC_KEYWORDS` or `TECH_KEYWORDS` dictionaries:

```python
# Add a new tech keyword group
TECH_KEYWORDS["Swift"] = ["swift", "swiftui", "xcode"]

# Add a new topic category
TOPIC_KEYWORDS["#swift"] = ["swift", "swiftui", "ios", "xcode"]
```

The keys are display labels; the values are lists of lowercase substrings to match against message text.

---

## Requirements

```
flask
click
rich
prettytable
```

Standard library only beyond these four packages - no NumPy, pandas, or other heavy dependencies. The full list is in [`requirements.txt`](requirements.txt).

---

## Contributing

Contributions are welcome! Here's how to get started:

1. **Fork** the repository on GitHub
2. **Create a branch** for your change:
   ```bash
   git checkout -b feature/my-improvement
   ```
3. **Make your changes** and commit them with a clear message
4. **Open a Pull Request** - please link or describe the issue it addresses

> For large changes (new features, refactors), please **open an issue first** to discuss the approach before writing code.

---

## License

MIT - see [LICENSE](LICENSE) for the full text.
