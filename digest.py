"""
AI-powered daily digest using the Gemini API.
Groups messages by day, samples them, sends to Gemini, renders structured output.
"""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import date
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from parser import Message, user_messages
from language import T
console = Console()
MAX_MSGS_PER_DAY = 200
MAX_MSG_CHARS = 150
MODEL = "gemini-2.5-flash-lite"
api_key = ">WRITE_YOUR_GEMINI_API_KEY_HERE<"
SYSTEM_PROMPT = """\
You are an analyst summarizing a WhatsApp group chat for a student hackathon called "AIS Hack 3.0" held in Aktobe, Kazakhstan.
The messages are in Russian, Kazakh, and some English.
Respond ONLY with a valid JSON object - no markdown, no backticks, no preamble. No extra text at all.
Required JSON structure:
{
  "total_messages": <integer>,
  "mood": "<one of: energetic | focused | tense | relaxed | chaotic>",
  "top_topics": ["<topic 1>", "<topic 2>", "<topic 3>"],
  "key_moments": ["<moment 1>", "<moment 2>", "<moment 3>"],
  "most_helpful": ["<name or number>", "<name or number>"],
  "summary": "<2-3 sentences in English describing the day>"
}
Rules:
- All text values must be in English.
- Each list item must be under 80 characters.
- "most_helpful" = users who answered questions, shared info, or helped others.
- "key_moments" = notable announcements, conflicts, funny moments, or decisions.
- "top_topics" = the main subjects discussed (not just #hashtags, real descriptions).
- Do NOT wrap the response in markdown code blocks.
"""
def _group_by_date(messages: list[Message]) -> dict[date, list[Message]]:
    groups: dict[date, list[Message]] = defaultdict(list)
    for m in user_messages(messages):
        groups[m.date].append(m)
    return dict(sorted(groups.items()))
def _sample_day(msgs: list[Message]) -> str:
    """Sample messages from a day and format them for the prompt."""
    step = max(1, len(msgs) // MAX_MSGS_PER_DAY)
    sampled = msgs[::step][:MAX_MSGS_PER_DAY]
    lines = []
    for m in sampled:
        text = m.text[:MAX_MSG_CHARS].replace("\n", " ")
        lines.append(f"[{m.dt.strftime('%H:%M')}] {m.author}: {text}")
    return "\n".join(lines)
def _call_api(day_text: str, day_label: str, api_key: str) -> dict:
    """Call the Gemini API and return parsed JSON result."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={api_key}"
    payload = {
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"Summarize messages from {day_label}:\n\n{day_text}"}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "maxOutputTokens": 1000
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read())
    raw = body["candidates"][0]["content"]["parts"][0]["text"].strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else parts[0]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
def _render_day(result: dict, day_label: str) -> None:
    """Render one day's digest as a Rich panel."""
    mood_raw = result.get("mood", "")
    mood_icons = {
        "energetic": "⚡", "focused": "🎯",
        "tense": "👀", "relaxed": "🦕", "chaotic": "🌪",
    }
    mood_icon = mood_icons.get(mood_raw, "💬")
    mood_key_map = {
        "energetic": "digest_mood_energetic", "focused": "digest_mood_focused",
        "tense": "digest_mood_tense", "relaxed": "digest_mood_relaxed",
        "chaotic": "digest_mood_chaotic",
    }
    mood_translated = T(mood_key_map.get(mood_raw, "digest_mood_relaxed"))
    total   = result.get("total_messages", "?")
    topics  = result.get("top_topics", [])
    moments = result.get("key_moments", [])
    helpful = result.get("most_helpful", [])
    summary = result.get("summary", "")
    C_A = "bright_yellow"
    C_D = "grey50"
    lines: list[str] = []
    lines.append(
        f"[{C_D}]{total} {T('digest_messages_count')}[/]  "
        f"[{C_A}]{mood_icon} {T('digest_mood_label')}:[/] {mood_translated}"
    )
    lines.append("")
    if topics:
        lines.append(f"[{C_A}]{T('digest_topics_label')}:[/]")
        for t in topics:
            lines.append(f"  [{C_D}]·[/] {t}")
        lines.append("")
    if moments:
        lines.append(f"[{C_A}]{T('digest_moments_label')}:[/]")
        for m in moments:
            lines.append(f"  [{C_D}]·[/] {m}")
        lines.append("")
    if helpful:
        names = "  /  ".join(helpful)
        lines.append(f"[{C_A}]{T('digest_helpful_label')}:[/]  {names}")
        lines.append("")
    if summary:
        lines.append(f"[{C_A}]{T('digest_summary_label')}:[/]")
        lines.append(f"  {summary}")
    body = "\n".join(lines)
    console.print(Panel(
        body,
        title=f"[bold cyan]{day_label}[/]",
        border_style="cyan",
        padding=(1, 2),
    ))
def generate_digest(
    messages: list[Message],
    days: list[date] | None = None,
) -> None:
    """
    Generate an AI digest for each day (or only the specified days).
    Requires GEMINI_API_KEY environment variable.
    """
    if not api_key:
        console.print(f"[bold red]GEMINI_API_KEY environment variable is not set.[/]")
        return
    grouped = _group_by_date(messages)
    if days:
        grouped = {d: v for d, v in grouped.items() if d in days}
    if not grouped:
        console.print(f"[yellow]{T('digest_no_messages')}[/]")
        return
    console.print(f"\n[bold cyan]{T('digest_generating', n=len(grouped))}[/]\n")
    for day, day_msgs in sorted(grouped.items()):
        day_label = day.strftime("%d %B %Y")
        console.print(
            f"  [grey50]{T('digest_processing', date=day_label, n=len(day_msgs))}[/]",
            end=" ",
        )
        try:
            day_text = _sample_day(day_msgs)
            result = _call_api(day_text, day_label, api_key)
            result["total_messages"] = len(day_msgs)
            console.print(f"[green]{T('digest_done')}[/]")
            _render_day(result, day_label)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            console.print(f"[red]{T('digest_error')}: HTTP {exc.code}[/]")
            try:
                detail = json.loads(body).get("error", {}).get("message", body[:120])
            except Exception:
                detail = body[:120]
            console.print(f"  [grey50]{detail}[/]")
        except json.JSONDecodeError as exc:
            console.print(f"[red]{T('digest_error')}: bad JSON - {exc}[/]")
        except Exception as exc:
            console.print(f"[red]{T('digest_error')}: {exc}[/]")
