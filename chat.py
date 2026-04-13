from prettytable import PrettyTable
from collections import Counter
from datetime import datetime
from pathlib import Path
import re
Message = list
CHAT_FILE: Path = Path(__file__).parent / "chat.txt"
_INVISIBLE = re.compile(r'[\u200E\u200F\u00A0\uFEFF\u202E\u202F]')
_MSG_PAT   = re.compile(
    r'^(\d{2}\.\d{2}\.\d{4}),\s*(\d{2}:\d{2})\s*-\s*'
    r'(?:(?P<author>[^:]+?)\s*:\s*(?P<message>.*)$|(?P<sys_message>.*)$)'
)
def top_users(messages: list[Message]) -> Counter:
    return Counter(
        author
        for _, author, _ in messages
        if author is not None
    )
def format_message(line: str) -> Message | str:
    line = _INVISIBLE.sub('', line).strip()
    m = _MSG_PAT.match(line)
    if not m:
        return line
    dt = datetime.strptime(f"{m.group(1)} {m.group(2)}", "%d.%m.%Y %H:%M")
    if m.group('author') is not None:
        author = m.group('author').strip() or None
        text   = (m.group('message') or '').strip()
    else:
        author = None
        text   = (m.group('sys_message') or '').strip()
    return [dt, author, text]
def read_chats() -> list[Message]:
    messages: list[Message] = []
    with open(CHAT_FILE, encoding='utf-8', errors='replace') as f:
        for line in f:
            result = format_message(line)
            if isinstance(result, str):
                if messages:
                    messages[-1][2] += f"\n{result}"
                continue
            messages.append(result)
    return messages
def main() -> None:
    messages = read_chats()
    counts   = top_users(messages)
    table = PrettyTable()
    table.field_names  = ["#", "User", "Messages"]
    table.align["User"]     = "l"
    table.align["Messages"] = "r"
    for rank, (user, count) in enumerate(counts.most_common(), start=1):
        table.add_row([rank, user, count])
    print(table)
    print(f"\nTotal: {sum(counts.values())} user messages from {len(counts)} participants")
if __name__ == '__main__':
    main()