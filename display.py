"""
Terminal rendering: tables, bar charts, and graphs using Rich.
"""
from __future__ import annotations
import math
from datetime import date
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint
from analytics import (
    WEEKDAY_NAMES,
    ChatStats,
    Edge,
    PenaltyEvent,
)
console = Console()
BAR_CHAR = '█'
HALF_BAR = '▌'
COLOR_MAIN   = 'cyan'
COLOR_ACCENT = 'bright_yellow'
COLOR_DIM    = 'grey50'
COLOR_GOOD   = 'green'
COLOR_BAD    = 'red'
COLOR_HEAD   = 'bold white'
BAR_WIDTH = 30
def _bar(value: int, max_val: int, width: int = BAR_WIDTH, color: str = COLOR_MAIN) -> Text:
    """Build a colored bar proportional to value/max_val."""
    if max_val == 0:
        filled = 0
    else:
        filled = round(value / max_val * width)
    filled = max(0, min(filled, width))
    bar_str = BAR_CHAR * filled + ' ' * (width - filled)
    t = Text()
    t.append(bar_str, style=color)
    return t
def _short_name(name: str, max_len: int = 22) -> str:
    if len(name) <= max_len:
        return name
    return name[:max_len - 1] + '…'
def render_summary(stats: ChatStats) -> None:
    start, end = stats.date_range
    duration = (end - start).days + 1
    content = (
        f"[{COLOR_ACCENT}]Messages[/]        {stats.user_messages:,} user  +  {stats.system_messages} system\n"
        f"[{COLOR_ACCENT}]Unique users[/]     {stats.unique_users}  (👻 {stats.ghost_count} ghosts - joined, never spoke)\n"
        f"[{COLOR_ACCENT}]Date range[/]       {start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}  ({duration} days)\n"
        f"[{COLOR_ACCENT}]Avg / day[/]        {stats.avg_messages_per_day} messages\n"
        f"[{COLOR_ACCENT}]Peak hour[/]        {stats.most_active_hour:02d}:00\n"
        f"[{COLOR_ACCENT}]Most active day[/]  {stats.most_active_day}\n"
        f"[{COLOR_ACCENT}]Media files[/]      {stats.total_media} attachments"
    )
    panel = Panel(content, title="[bold cyan]  Chat Overview[/]", border_style="cyan", padding=(1, 2))
    console.print(panel)
def render_top_users(data: list[tuple[str, int]], title: str = "Top Users") -> None:
    table = Table(
        title=title,
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("#", style=COLOR_DIM, width=4, justify='right')
    table.add_column("User", style=COLOR_ACCENT, min_width=24)
    table.add_column("Messages", justify='right', style=COLOR_MAIN, width=10)
    table.add_column("Activity", min_width=BAR_WIDTH + 2)
    if not data:
        console.print("[yellow]No data.[/]")
        return
    max_count = data[0][1]
    for rank, (user, count) in enumerate(data, start=1):
        bar = _bar(count, max_count)
        table.add_row(str(rank), _short_name(user), str(count), bar)
    console.print(table)
def render_hourly_activity(by_hour: dict[int, int]) -> None:
    console.print(Panel(
        "",
        title="[bold cyan]  Activity by Hour[/]",
        border_style="cyan",
        padding=(0, 0),
        expand=False,
    ))
    max_val = max(by_hour.values(), default=1)
    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Hour", style=COLOR_DIM, width=6, justify='right')
    table.add_column("Bar", min_width=BAR_WIDTH)
    table.add_column("Count", style=COLOR_MAIN, width=6, justify='right')
    for hour in range(24):
        count = by_hour.get(hour, 0)
        if 0 <= hour < 6:
            color = 'blue'
        elif 6 <= hour < 12:
            color = 'green'
        elif 12 <= hour < 18:
            color = 'yellow'
        else:
            color = 'red'
        bar = _bar(count, max_val, color=color)
        table.add_row(f"{hour:02d}:00", bar, str(count))
    console.print(table)
    console.print(
        f"  [{COLOR_DIM}][blue]■[/] 00–05 Night  "
        f"[green]■[/] 06–11 Morning  "
        f"[yellow]■[/] 12–17 Afternoon  "
        f"[red]■[/] 18–23 Evening[/]"
    )
def render_weekday_activity(by_weekday: dict[int, int]) -> None:
    max_val = max(by_weekday.values(), default=1)
    table = Table(
        title="Activity by Day of Week",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("Day", style=COLOR_ACCENT, width=5)
    table.add_column("Activity", min_width=BAR_WIDTH)
    table.add_column("Count", style=COLOR_MAIN, width=8, justify='right')
    for d in range(7):
        count = by_weekday.get(d, 0)
        color = 'bright_cyan' if d >= 5 else COLOR_MAIN
        bar = _bar(count, max_val, color=color)
        table.add_row(WEEKDAY_NAMES[d], bar, str(count))
    console.print(table)
def render_daily_activity(by_date: dict[date, int]) -> None:
    if not by_date:
        console.print("[yellow]No data.[/]")
        return
    max_val = max(by_date.values(), default=1)
    table = Table(
        title="Activity by Date",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("Date", style=COLOR_ACCENT, width=12)
    table.add_column("Day", style=COLOR_DIM, width=5)
    table.add_column("Activity", min_width=BAR_WIDTH)
    table.add_column("Count", style=COLOR_MAIN, width=8, justify='right')
    for d, count in by_date.items():
        wd = WEEKDAY_NAMES[d.weekday()]
        color = 'bright_cyan' if d.weekday() >= 5 else COLOR_MAIN
        bar = _bar(count, max_val, color=color)
        table.add_row(d.strftime('%d %b %Y'), wd, bar, str(count))
    console.print(table)
def render_interaction_graph(edges: list[Edge], top_n: int = 15) -> None:
    edges = edges[:top_n]
    if not edges:
        console.print("[yellow]No interaction data.[/]")
        return
    max_weight = edges[0].weight
    table = Table(
        title=f"Top {len(edges)} User Interactions (reply chains)",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("#", style=COLOR_DIM, width=4, justify='right')
    table.add_column("Replied", style=COLOR_ACCENT, min_width=22)
    table.add_column("→", style=COLOR_DIM, width=3)
    table.add_column("To", style=COLOR_MAIN, min_width=22)
    table.add_column("Times", justify='right', style='bright_yellow', width=7)
    table.add_column("Strength", min_width=20)
    for i, edge in enumerate(edges, start=1):
        bar = _bar(edge.weight, max_weight, width=20)
        table.add_row(
            str(i),
            _short_name(edge.source),
            '→',
            _short_name(edge.target),
            str(edge.weight),
            bar,
        )
    console.print(table)
    console.print(
        f"  [{COLOR_DIM}]Interaction = B sent a message within 2 min after A[/]\n"
    )
def render_ghosts(ghosts: list[str]) -> None:
    if not ghosts:
        console.print("[green]No ghost participants found![/]")
        return
    table = Table(
        title=f"👻 Ghost Participants ({len(ghosts)} total)",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("#", style=COLOR_DIM, width=4, justify='right')
    table.add_column("Identifier", style=COLOR_DIM)
    for i, g in enumerate(ghosts, start=1):
        table.add_row(str(i), g)
    console.print(table)
def render_penalties(events: list[PenaltyEvent]) -> None:
    if not events:
        console.print("[green]No penalty events found.[/]")
        return
    table = Table(
        title=f"   Penalty / Bonus Events ({len(events)} total)",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("Time", style=COLOR_DIM, width=11)
    table.add_column("Issuer", style=COLOR_ACCENT, min_width=22)
    table.add_column("Δ Points", justify='right', width=9)
    table.add_column("Message", style=COLOR_DIM, max_width=50)
    for ev in events:
        amount_str = f"{ev.amount:+d}"
        color = COLOR_GOOD if ev.amount > 0 else COLOR_BAD
        table.add_row(
            ev.dt,
            _short_name(ev.issuer),
            Text(amount_str, style=color),
            ev.raw_text[:80],
        )
    console.print(table)
def render_media(data: list[tuple[str, int]]) -> None:
    if not data:
        console.print("[yellow]No media attachments found.[/]")
        return
    render_top_users(data, title="📎 Media Senders (files attached)")
def render_tech_stack(data: list[tuple[str, int]]) -> None:
    if not data:
        console.print("[yellow]No tech mentions found.[/]")
        return
    table = Table(
        title="   Tech Stack Mentions",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("Technology", style=COLOR_ACCENT, min_width=16)
    table.add_column("Mentions", justify='right', style=COLOR_MAIN, width=10)
    table.add_column("Popularity", min_width=BAR_WIDTH)
    max_count = data[0][1] if data else 1
    for tech, count in data:
        bar = _bar(count, max_count)
        table.add_row(tech, str(count), bar)
    console.print(table)
def render_topics(data: dict[str, int]) -> None:
    if not data:
        console.print("[yellow]No topic data.[/]")
        return
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    max_count = sorted_data[0][1] if sorted_data else 1
    table = Table(
        title="   Topic Distribution",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style=COLOR_HEAD,
        border_style=COLOR_DIM,
    )
    table.add_column("Tag", style=COLOR_ACCENT, min_width=12)
    table.add_column("Messages", justify='right', style=COLOR_MAIN, width=10)
    table.add_column("Share", justify='right', style=COLOR_DIM, width=7)
    table.add_column("Distribution", min_width=BAR_WIDTH)
    total = sum(data.values())
    for tag, count in sorted_data:
        pct = f"{count/total*100:.1f}%" if total else "0%"
        bar = _bar(count, max_count)
        table.add_row(tag, str(count), pct, bar)
    console.print(table)
