# chat-analyzer

A WhatsApp chat log analytics CLI tool. Built around the AIS Hack 3.0 group chat, but works with any WhatsApp export.

## Requirements

- Python 3.12+
- Dependencies: `pip install -r requirements.txt`

## Setup

```bash
pip install -r requirements.txt
```

Place your WhatsApp export file (e.g. `chat.txt`) in the same folder, or pass it with `-f`.

## Commands

### `summary` — Overall statistics

```bash
python main.py summary
python main.py summary -f /path/to/other_chat.txt
```

Shows: total messages, unique users, date range, avg per day, peak hour, most active weekday, media count, ghost count.

---

### `users` — Top message senders

```bash
python main.py users
python main.py users --top 30
```

Options:
- `-n / --top`  Number of users to display (default: 20)

---

### `activity` — Time-based charts

```bash
python main.py activity                  # all three charts
python main.py activity --mode hour      # messages by hour (0–23)
python main.py activity --mode weekday   # messages by day of week
python main.py activity --mode date      # messages per calendar date
```

Options:
- `-m / --mode`  `hour` | `weekday` | `date` | `all` (default: `all`)

---

### `graph` — Interaction graph

```bash
python main.py graph
python main.py graph --top 20 --window 60
```

Shows who replies to whom most often. Two users are "interacting" when one sends a message within the reply window after the other.

Options:
- `-n / --top`     Number of pairs (default: 15)
- `-w / --window`  Reply window in seconds (default: 120)

---

### `topics` — Topic & tech-stack classification

```bash
python main.py topics
python main.py topics --no-tech    # skip tech stack table
```

Classifies messages into tags: `#rules`, `#tasks`, `#linux`, `#games`, `#infra`, `#general`, `#news`, `#media`.
Also extracts technology mentions: Python, C++, Rust, AI/ML, Linux distros, etc.

---

### `media` — Media leaderboard

```bash
python main.py media
python main.py media --top 10
```

Counts image/video/sticker/file attachments per user.

---

### `ghosts` — Silent members

```bash
python main.py ghosts
```

Lists participants who appeared in system join messages but never sent a chat message.

---

### `penalties` — Point events

```bash
python main.py penalties
```

Extracts any message containing "балл / баллов" and parses the point delta.

---

### `digest` — AI daily summary *(requires API key)*

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python main.py digest                        # all days
python main.py digest --date 2026-03-29      # one specific day
```

Calls the Anthropic API to generate a structured summary for each day:
- Top topics
- Key moments
- Most helpful participants
- Overall mood
- Plain-English summary

Options:
- `-d / --date`  Target date in `YYYY-MM-DD` format

---

### `all` — Run everything

```bash
python main.py all
python main.py all --top 20
```

Runs all analyses in sequence (except the AI digest, which requires an API key).

---

## File format

The tool expects a standard WhatsApp group export in `.txt` format:

```
29.03.2026, 05:28 - +7 775 186 9650: Когда задачи скинут?
29.03.2026, 05:29 - +7 775 186 9650: STK-20260329-WA0000.webp (файл добавлен)
29.03.2026, 07:30 - ‎~ Yeraly добавлен(-а)
```

Multi-line messages, invisible Unicode characters, and system events are all handled automatically.

## Project structure

```
chat_analyzer/
├── main.py          # CLI entrypoint (Click)
├── parser.py        # WhatsApp log parser
├── analytics.py     # All stat computations (pure functions)
├── display.py       # Terminal rendering (Rich tables & charts)
├── digest.py        # AI digest via Anthropic API
├── requirements.txt
└── README.md
```
