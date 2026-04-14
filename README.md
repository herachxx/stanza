# stanza

A command-line analytics tool for WhatsApp group chat exports. Drop in a `.txt` export and get rich terminal dashboards: message stats, activity charts, interaction graphs, topic classification, media leaderboards, and an AI-powered daily digest.

Built for the **AIS Hack 3.0** group chat in Aktobe, Kazakhstan - works with any standard WhatsApp export.

```bash
python main.py summary
python main.py activity --mode hour
python main.py digest --date 2026-03-29
```

## Commands

| Command | What it does |
|---|---|
| `summary` | Total messages, date range, peak hour, active weekday, ghost count |
| `users` | Ranked leaderboard of most active participants |
| `activity` | Bar charts broken down by hour, weekday, or calendar date |
| `graph` | Interaction pairs - who replies to whom most often |
| `topics` | Keyword-based topic tags and tech-stack mentions |
| `media` | Attachment leaderboard: images, videos, stickers, files |
| `ghosts` | Members who joined but never sent a message |
| `penalties` | Parses point/penalty events from messages |
| `digest` | AI-generated daily summary via Gemini *(API key required)* |
| `all` | Runs all of the above in one shot |

The UI is powered by [Rich](https://github.com/Textualize/rich) - colored tables, inline bar charts, styled panels. A language picker at startup supports **English**, **Русский**, **Қазақша**, and **Qazaqsha**.

## Requirements

- Python 3.12+
- Windows, macOS, or Linux

## Installation

```bash
cd stanza
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Quick Start

Export your WhatsApp group chat: open the group → **⋮ → More → Export chat → Without media**. Save it as `chat.txt` in the project folder, then:

```bash
python main.py summary
```

All commands accept `-f` to point at a different file:

```bash
python main.py summary -f /path/to/my_chat.txt
```

## Command Reference

### `summary`
```bash
python main.py summary
```
Displays total messages, unique participants, date range, average messages/day, peak hour, most active weekday, media count, and ghost count.

### `users`
```bash
python main.py users
python main.py users --top 30        # default: 20
```

### `activity`
```bash
python main.py activity              # all three charts
python main.py activity --mode hour
python main.py activity --mode weekday
python main.py activity --mode date
```
`--mode` accepts `hour`, `weekday`, `date`, or `all`.

### `graph`
```bash
python main.py graph
python main.py graph --top 20 --window 60
```
Two users are "interacting" when one messages within `--window` seconds (default `120`) of the other. Shows the top `--top` pairs (default `15`).

### `topics`
```bash
python main.py topics
python main.py topics --no-tech      # skip tech-stack table
```
Tags messages as `#rules` · `#tasks` · `#linux` · `#games` · `#infra` · `#general` · `#news` · `#media`.
Also surfaces tech mentions: Python, JavaScript, C++, Rust, Go, SQL, Docker, Linux distros, AI/ML tools, Git, and more.

### `media`
```bash
python main.py media
python main.py media --top 10        # default: 20
```

### `ghosts`
```bash
python main.py ghosts
```
Lists participants who appear in system join messages but have zero sent messages.

### `penalties`
```bash
python main.py penalties
```
Scans for messages containing `балл` / `баллов` and extracts the associated point delta.

### `digest` *(requires Gemini API key)*
```bash
export GEMINI_API_KEY=your-key-here
python main.py digest                        # all days
python main.py digest --date 2026-03-29      # one specific day
```
Calls **Gemini 2.5 Flash** to generate a structured summary per day: mood, top topics, key moments, most helpful participants, and a short plain-English summary.

> The Gemini SDK is not in `requirements.txt` by default. Install it with `pip install google-genai`.

### `all`
```bash
python main.py all
python main.py all --top 20
```
Runs every command except `digest` in sequence. `--top` is passed through to `users` and `media`.

## Chat File Format

The parser expects a standard WhatsApp group export:

```
29.03.2026, 05:28 - +7 775 186 9650: Когда задачи скинут?
29.03.2026, 05:29 - +7 775 186 9650: STK-20260329-WA0000.webp (файл добавлен)
29.03.2026, 07:30 - ‎~ Yeraly добавлен(-а)
```

Handled automatically: multi-line messages, invisible Unicode characters (`\u200E`, `\uFEFF`, `\u200B`, …), system events, both `.` and `/` date separators, and media attachment lines.

## Project Structure

```
stanza/
├── main.py          # CLI entrypoint (Click commands, language picker)
├── parser.py        # WhatsApp log parser (regex + dataclasses)
├── analytics.py     # Pure stat computations (Counter, dataclasses)
├── display.py       # Terminal rendering (Rich tables, bar charts, panels)
├── digest.py        # AI digest via Gemini API
├── language.py      # i18n - EN, RU, KZ-Cyrillic, KZ-Latin
├── chat.py          # Legacy helper (PrettyTable-based, unused by main.py)
├── requirements.txt
└── README.md
```

## Internationalization

At startup, stanza prompts you to pick a language. All UI strings are translated:

| Code | Language |
|---|---|
| `en` | English |
| `ru` | Русский |
| `kz_c` | Қазақша (Cyrillic) |
| `kz_l` | Qazaqsha (Latin) |

## Known Issues & Suggestions

**`digest.py` hardcodes the API key** as a placeholder string instead of reading from the environment. Replace the literal with `os.environ.get("GEMINI_API_KEY", "")` to match the documented usage.

**`chat.py` is dead code.** It duplicates parsing logic from `parser.py` and is never imported by `main.py`. Safe to delete.

**Missing graceful error for `google-genai`.** Running `digest` without the SDK installed raises a raw `ImportError`. A `try/except ImportError` with a friendly message would improve the experience significantly.

**`results.txt` is always written to the project directory.** Consider making this opt-in with a `--save` flag, or letting the user specify an output path.
