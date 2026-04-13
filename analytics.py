"""
Analytics computations over parsed messages.
"""
from __future__ import annotations
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import NamedTuple
from parser import Message, user_messages
WEEKDAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
WEEKDAY_NAMES_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
TECH_KEYWORDS: dict[str, list[str]] = {
    'Python':     ['python', 'питон', 'пайтон', 'django', 'flask', 'fastapi', 'pandas', 'numpy'],
    'C++':        ['c++', 'cpp', 'плюсы', 'плюсах'],
    'JavaScript': ['javascript', 'js', 'node', 'nodejs', 'react', 'vue', 'typescript', 'ts'],
    'Lua':        ['lua'],
    'Rust':       ['rust', 'раст'],
    'Go':         ['golang', ' go '],
    'SQL':        ['sql', 'postgres', 'postgresql', 'mysql', 'sqlite'],
    'Docker':     ['docker', 'докер', 'контейнер'],
    'Linux':      ['linux', 'линукс', 'arch', 'nixos', 'fedora', 'debian', 'ubuntu'],
    'AI/ML':      ['chatgpt', 'gemini', 'gpt', 'llm', 'нейро', 'нейросет', 'ai', 'ml', 'машинное обучение'],
    'Git':        ['github', 'gitlab', 'git'],
    'Telegram':   ['telegram', 'тг', 'телеграм'],
}
TOPIC_KEYWORDS: dict[str, list[str]] = {
    '#rules':   ['правило', 'правила', 'правил', 'штраф', 'балл', 'нарушение', 'санкц'],
    '#tasks':   ['задач', 'задание', 'deadline', 'дедлайн', 'сдать', 'сдавать', 'кейс'],
    '#linux':   ['linux', 'линукс', 'arch', 'nixos', 'fedora', 'debian', 'ubuntu', 'дистр'],
    '#games':   ['clash', 'royale', 'chess', 'dota', 'standoff', 'майнкрафт', 'minecraft', 'игр', 'игра'],
    '#infra':   ['сервер', 'server', 'deploy', 'деплой', 'docker', 'докер', 'база данных', 'бд'],
    '#general': ['привет', 'здравствуй', 'утро', 'вечер', 'как дела', 'норм', 'ок'],
    '#news':    ['новост', 'объявл', 'внимание', 'важно'],
    '#media':   ['файл добавлен', 'webp', 'jpg', 'mp4'],
}
def top_users(messages: list[Message], n: int = 20) -> list[tuple[str, int]]:
    """Return (author, count) sorted by count desc."""
    um = user_messages(messages)
    counter = Counter(m.author for m in um)
    return counter.most_common(n)
def activity_by_hour(messages: list[Message]) -> dict[int, int]:
    """Messages per hour (0–23)."""
    counter: dict[int, int] = {h: 0 for h in range(24)}
    for m in user_messages(messages):
        counter[m.hour] += 1
    return counter
def activity_by_weekday(messages: list[Message]) -> dict[int, int]:
    """Messages per weekday (0=Mon … 6=Sun)."""
    counter: dict[int, int] = {d: 0 for d in range(7)}
    for m in user_messages(messages):
        counter[m.weekday] += 1
    return counter
def activity_by_date(messages: list[Message]) -> dict[date, int]:
    """Messages per calendar date."""
    counter: dict[date, int] = defaultdict(int)
    for m in user_messages(messages):
        counter[m.date] += 1
    if not counter:
        return {}
    min_d = min(counter)
    max_d = max(counter)
    d = min_d
    while d <= max_d:
        counter.setdefault(d, 0)
        d += timedelta(days=1)
    return dict(sorted(counter.items()))
def peak_hours(messages: list[Message], top_n: int = 3) -> list[tuple[int, int]]:
    """Return the top N busiest hours as (hour, count) pairs."""
    by_hour = activity_by_hour(messages)
    return sorted(by_hour.items(), key=lambda x: x[1], reverse=True)[:top_n]
class Edge(NamedTuple):
    source: str
    target: str
    weight: int
def build_interaction_graph(
    messages: list[Message],
    window_seconds: int = 120,
) -> list[Edge]:
    """
    Approximate reply graph: if user B sends a message within `window_seconds`
    after user A (and B ≠ A), count it as B→A interaction.

    Returns a list of Edge(source, target, weight).
    """
    um = user_messages(messages)
    pair_counts: Counter[tuple[str, str]] = Counter()
    for i in range(1, len(um)):
        cur = um[i]
        prev = um[i - 1]
        if cur.author == prev.author:
            continue
        delta = (cur.dt - prev.dt).total_seconds()
        if 0 <= delta <= window_seconds:
            pair_counts[(cur.author, prev.author)]+= 1  # type: ignore[index]
    return [Edge(s, t, w) for (s, t), w in pair_counts.most_common()]
def top_interactions(messages: list[Message], n: int = 15, window_seconds: int = 120) -> list[Edge]:
    edges = build_interaction_graph(messages, window_seconds)
    return edges[:n]
def ghost_participants(messages: list[Message]) -> list[str]:
    """
    Return phone numbers / names that appear in system join messages
    but never sent a user message.
    """
    joined: set[str] = set()
    for m in messages:
        if m.is_system:
            # "‎+7 747 963 3712 присоединился(-ась) из сообщества"
            joined_match = re.match(r'^(\+\d[\d\s]+|\S+)\s+присоединил', m.text)
            if joined_match:
                joined.add(joined_match.group(1).strip())
    speakers: set[str] = {m.author for m in user_messages(messages)}
    return sorted(joined - speakers)
class PenaltyEvent(NamedTuple):
    dt: str
    issuer: str
    amount: int
    raw_text: str
PENALTY_PAT = re.compile(
    r'([+-]?\s*\d+)\s*балл',
    re.IGNORECASE,
)
def extract_penalties(messages: list[Message]) -> list[PenaltyEvent]:
    """Extract messages that mention point changes (балл/баллов)."""
    events: list[PenaltyEvent] = []
    for m in user_messages(messages):
        match = PENALTY_PAT.search(m.text)
        if match:
            raw_num = match.group(1).replace(' ', '')
            try:
                amount = int(raw_num)
            except ValueError:
                continue
            events.append(PenaltyEvent(
                dt=m.dt.strftime('%d.%m %H:%M'),
                issuer=m.author or '?',
                amount=amount,
                raw_text=m.text.strip(),
            ))
    return events
def media_by_user(messages: list[Message]) -> list[tuple[str, int]]:
    """Count media attachments (files added) per user."""
    counter: Counter[str] = Counter()
    for m in user_messages(messages):
        if m.attachments:
            counter[m.author] += len(m.attachments)  # type: ignore[index]
    return counter.most_common()
def classify_message(text: str) -> list[str]:
    """Return matching topic tags for a message text."""
    text_lower = text.lower()
    tags: list[str] = []
    for tag, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            tags.append(tag)
    return tags or ['#general']
def topic_distribution(messages: list[Message]) -> dict[str, int]:
    """Count how many messages fall under each topic tag."""
    counts: Counter[str] = Counter()
    for m in user_messages(messages):
        if not m.has_text():
            continue
        for tag in classify_message(m.text):
            counts[tag] += 1
    return dict(counts.most_common())
def extract_tech_stack(messages: list[Message]) -> list[tuple[str, int]]:
    """Count technology mentions across all user messages."""
    counts: Counter[str] = Counter()
    for m in user_messages(messages):
        text_lower = m.text.lower()
        for tech, keywords in TECH_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                counts[tech] += 1
    return counts.most_common()
class ChatStats(NamedTuple):
    total_messages: int
    user_messages: int
    system_messages: int
    unique_users: int
    date_range: tuple[date, date]
    avg_messages_per_day: float
    most_active_hour: int
    most_active_day: str
    total_media: int
    ghost_count: int
def compute_stats(messages: list[Message]) -> ChatStats:
    um = user_messages(messages)
    all_dates = [m.date for m in um]
    date_range = (min(all_dates), max(all_dates)) if all_dates else (date.today(), date.today())
    num_days = max((date_range[1] - date_range[0]).days + 1, 1)
    by_hour = activity_by_hour(messages)
    by_weekday = activity_by_weekday(messages)
    most_active_hour = max(by_hour, key=lambda h: by_hour[h])
    most_active_wd = max(by_weekday, key=lambda d: by_weekday[d])
    total_media = sum(len(m.attachments) for m in um)
    return ChatStats(
        total_messages=len(messages),
        user_messages=len(um),
        system_messages=len(messages) - len(um),
        unique_users=len({m.author for m in um}),
        date_range=date_range,
        avg_messages_per_day=round(len(um) / num_days, 1),
        most_active_hour=most_active_hour,
        most_active_day=WEEKDAY_NAMES[most_active_wd],
        total_media=total_media,
        ghost_count=len(ghost_participants(messages)),
    )
