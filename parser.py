"""
WhatsApp chat log parser.
Handles the export format: DD.MM.YYYY, HH:MM - Author: text
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
INVISIBLE = re.compile(r'[\u200E\u200F\u00A0\uFEFF\u202E\u202F\u200B\u2060]')
MSG_PAT = re.compile(
    r'^(\d{2}[./]\d{2}[./]\d{4}),\s*(\d{2}:\d{2})\s*-\s*'
    r'(?:(?P<author>[^:]+?)\s*:\s*(?P<text>.*)$|(?P<sys_text>.*)$)'
)
@dataclass
class Message:
    dt: datetime
    author: str | None
    text: str
    is_system: bool = False
    attachments: list[str] = field(default_factory=list)
    @property
    def hour(self) -> int:
        return self.dt.hour
    @property
    def weekday(self) -> int:
        """0=Monday … 6=Sunday"""
        return self.dt.weekday()
    @property
    def date(self):
        return self.dt.date()
    def has_text(self) -> bool:
        stripped = self.text.strip()
        if re.fullmatch(r'\S+\s+\(файл добавлен\)', stripped):
            return False
        return bool(stripped)
def _clean(line: str) -> str:
    return INVISIBLE.sub('', line)
def _parse_line(line: str) -> Message | str:
    """
    Return a Message if the line starts a new message, or a plain str
    (continuation of the previous message).
    """
    line = _clean(line).strip()
    m = MSG_PAT.match(line)
    if not m:
        return line
    date_str = m.group(1)
    time_str = m.group(2)
    date_str = date_str.replace('/', '.')
    dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    if m.group('author') is not None:
        author = m.group('author').strip() or None
        text = (m.group('text') or '').strip()
        is_system = False
    else:
        author = None
        text = (m.group('sys_text') or '').strip()
        is_system = True
    attachments: list[str] = []
    attach_pat = re.compile(r'(\S+\.(webp|jpg|jpeg|png|mp4|pdf|zip|gif|opus|aac|mp3))\s+\(файл добавлен\)', re.IGNORECASE)
    for match in attach_pat.finditer(text):
        attachments.append(match.group(1))
    return Message(dt=dt, author=author, text=text, is_system=is_system, attachments=attachments)
def parse_file(path: str | Path) -> list[Message]:
    """Parse a WhatsApp export file and return a list of Messages."""
    path = Path(path)
    messages: list[Message] = []
    with open(path, encoding='utf-8', errors='replace') as fh:
        for raw_line in fh:
            result = _parse_line(raw_line)
            if isinstance(result, str):
                if messages:
                    messages[-1].text += f"\n{result}"
            else:
                messages.append(result)
    return messages
def user_messages(messages: list[Message]) -> list[Message]:
    """Filter to only real user messages (not system events)."""
    return [m for m in messages if m.author is not None]
