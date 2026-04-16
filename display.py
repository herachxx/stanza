from __future__ import annotations
from datetime import date
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from analytics import ChatStats, Edge, PenaltyEvent
from language import T
console = Console()
BAR_CHAR = "█"
C_MAIN   = "cyan"
C_ACCENT = "bright_yellow"
C_DIM    = "grey50"
C_GOOD   = "green"
C_BAD    = "red"
C_HEAD   = "bold white"
BAR_W    = 28
def _bar(value: int, max_val: int, width: int = BAR_W, color: str = C_MAIN) -> Text:
    filled = 0 if max_val == 0 else round(value / max_val * width)
    filled = max(0, min(filled, width))
    t = Text()
    t.append(BAR_CHAR * filled, style=color)
    t.append(" " * (width - filled), style="")
    return t
def _short(name: str, n: int = 22) -> str:
    return name if len(name) <= n else name[: n - 1] + "…"
def render_summary(stats: ChatStats) -> None:
    start, end = stats.date_range
    duration = (end - start).days + 1
    content = (
        f"[{C_ACCENT}]{T('summary_messages')}[/]       "
        f"{stats.user_messages:,} {T('summary_user')}  +  {stats.system_messages} {T('summary_system')}\n"
        f"[{C_ACCENT}]{T('summary_unique_users')}[/]  "
        f"{stats.unique_users}  "
        f"[{C_DIM}]({stats.ghost_count} - {T('summary_ghosts_note')})[/]\n"
        f"[{C_ACCENT}]{T('summary_date_range')}[/]       "
        f"{start.strftime('%d %b %Y')} → {end.strftime('%d %b %Y')}  "
        f"[{C_DIM}]({duration} {T('summary_days')})[/]\n"
        f"[{C_ACCENT}]{T('summary_avg_day')}[/]      {stats.avg_messages_per_day}\n"
        f"[{C_ACCENT}]{T('summary_peak_hour')}[/]       {stats.most_active_hour:02d}:00\n"
        f"[{C_ACCENT}]{T('summary_active_day')}[/]   {stats.most_active_day}\n"
        f"[{C_ACCENT}]{T('summary_media')}[/]       {stats.total_media}"
    )
    console.print(Panel(
        content,
        title=f"[bold {C_MAIN}]{T('section_summary')}[/]",
        border_style=C_MAIN,
        padding=(1, 2),
    ))
def render_top_users(data: list[tuple[str, int]], title: str | None = None) -> None:
    if not data:
        console.print(f"[{C_DIM}]{T('no_data')}[/]")
        return
    tbl = Table(
        title=title or T("title_top_users"),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_rank"),     style=C_DIM,    width=4,          justify="right")
    tbl.add_column(T("col_user"),     style=C_ACCENT, min_width=24)
    tbl.add_column(T("col_messages"), style=C_MAIN,   width=10,         justify="right")
    tbl.add_column(T("col_activity"), min_width=BAR_W + 2)
    max_c = data[0][1]
    for rank, (user, count) in enumerate(data, 1):
        tbl.add_row(str(rank), _short(user), str(count), _bar(count, max_c))
    console.print(tbl)
def render_hourly_activity(by_hour: dict[int, int]) -> None:
    max_v = max(by_hour.values(), default=1)
    tbl = Table(
        title=T("title_hourly"),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_hour"),  style=C_DIM,  width=6,  justify="right")
    tbl.add_column(T("col_activity"), min_width=BAR_W)
    tbl.add_column(T("col_count"), style=C_MAIN, width=7,  justify="right")
    colors = {range(0, 6): "blue", range(6, 12): "green",
              range(12, 18): "yellow", range(18, 24): "red"}
    for h in range(24):
        c = next((v for r, v in colors.items() if h in r), C_MAIN)
        tbl.add_row(f"{h:02d}:00", _bar(by_hour.get(h, 0), max_v, color=c), str(by_hour.get(h, 0)))
    console.print(tbl)
    console.print(
        f"  [{C_DIM}][blue]{BAR_CHAR}[/] {T('time_night')}   "
        f"[green]{BAR_CHAR}[/] {T('time_morning')}   "
        f"[yellow]{BAR_CHAR}[/] {T('time_afternoon')}   "
        f"[red]{BAR_CHAR}[/] {T('time_evening')}[/]"
    )
def render_weekday_activity(by_weekday: dict[int, int]) -> None:
    max_v = max(by_weekday.values(), default=1)
    names = T.weekday_names()
    tbl = Table(
        title=T("title_weekday"),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_day"),      style=C_ACCENT, width=5)
    tbl.add_column(T("col_activity"), min_width=BAR_W)
    tbl.add_column(T("col_count"),    style=C_MAIN,   width=8, justify="right")
    for d in range(7):
        count = by_weekday.get(d, 0)
        color = "bright_cyan" if d >= 5 else C_MAIN
        tbl.add_row(names[d], _bar(count, max_v, color=color), str(count))
    console.print(tbl)
def render_daily_activity(by_date: dict[date, int]) -> None:
    if not by_date:
        console.print(f"[{C_DIM}]{T('no_data')}[/]")
        return
    max_v = max(by_date.values(), default=1)
    names = T.weekday_names()
    tbl = Table(
        title=T("title_daily"),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_date"),     style=C_ACCENT, width=13)
    tbl.add_column(T("col_day"),      style=C_DIM,    width=5)
    tbl.add_column(T("col_activity"), min_width=BAR_W)
    tbl.add_column(T("col_count"),    style=C_MAIN,   width=8, justify="right")
    for d, count in by_date.items():
        color = "bright_cyan" if d.weekday() >= 5 else C_MAIN
        tbl.add_row(d.strftime("%d %b %Y"), names[d.weekday()], _bar(count, max_v, color=color), str(count))
    console.print(tbl)
def render_interaction_graph(edges: list[Edge], top_n: int = 15) -> None:
    edges = edges[:top_n]
    if not edges:
        console.print(f"[{C_DIM}]{T('no_interactions')}[/]")
        return
    max_w = edges[0].weight
    tbl = Table(
        title=T("title_interactions", n=len(edges)),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_rank"),     style=C_DIM,    width=4, justify="right")
    tbl.add_column(T("col_replied"),  style=C_ACCENT, min_width=22)
    tbl.add_column("→",               style=C_DIM,    width=3)
    tbl.add_column(T("col_to"),       style=C_MAIN,   min_width=22)
    tbl.add_column(T("col_times"),    style=C_ACCENT, width=7, justify="right")
    tbl.add_column(T("col_strength"), min_width=18)
    for i, e in enumerate(edges, 1):
        tbl.add_row(str(i), _short(e.source), "→", _short(e.target),
                    str(e.weight), _bar(e.weight, max_w, width=18))
    console.print(tbl)
    console.print(f"  [{C_DIM}]{T('interaction_note')}[/]\n")
def render_ghosts(ghosts: list[str]) -> None:
    if not ghosts:
        console.print(f"[{C_GOOD}]{T('no_ghosts')}[/]")
        return
    tbl = Table(
        title=T("title_ghosts", n=len(ghosts)),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_rank"),       style=C_DIM, width=4, justify="right")
    tbl.add_column(T("col_identifier"), style=C_DIM)
    for i, g in enumerate(ghosts, 1):
        tbl.add_row(str(i), g)
    console.print(tbl)
def render_penalties(events: list[PenaltyEvent]) -> None:
    if not events:
        console.print(f"[{C_GOOD}]{T('no_penalties')}[/]")
        return
    tbl = Table(
        title=T("title_penalties", n=len(events)),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_time"),    style=C_DIM,    width=11)
    tbl.add_column(T("col_issuer"),  style=C_ACCENT, min_width=22)
    tbl.add_column(T("col_points"),  width=9,        justify="right")
    tbl.add_column(T("col_message"), style=C_DIM,    max_width=50)
    for ev in events:
        amt = f"{ev.amount:+d}"
        color = C_GOOD if ev.amount > 0 else C_BAD
        tbl.add_row(ev.dt, _short(ev.issuer), Text(amt, style=color), ev.raw_text[:80])
    console.print(tbl)
def render_media(data: list[tuple[str, int]]) -> None:
    if not data:
        console.print(f"[{C_DIM}]{T('no_media')}[/]")
        return
    render_top_users(data, title=T("title_media"))
def render_tech_stack(data: list[tuple[str, int]]) -> None:
    if not data:
        console.print(f"[{C_DIM}]{T('no_tech')}[/]")
        return
    max_c = data[0][1]
    tbl = Table(
        title=T("title_tech"),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_tech"),       style=C_ACCENT, min_width=16)
    tbl.add_column(T("col_mentions"),   style=C_MAIN,   width=10, justify="right")
    tbl.add_column(T("col_popularity"), min_width=BAR_W)
    for tech, count in data:
        tbl.add_row(tech, str(count), _bar(count, max_c))
    console.print(tbl)
def render_topics(data: dict[str, int]) -> None:
    if not data:
        console.print(f"[{C_DIM}]{T('no_topics')}[/]")
        return
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    max_c = sorted_data[0][1]
    total = sum(data.values())
    tbl = Table(
        title=T("title_topics"),
        box=box.SIMPLE_HEAVY, show_header=True,
        header_style=C_HEAD, border_style=C_DIM,
    )
    tbl.add_column(T("col_tag"),      style=C_ACCENT, min_width=12)
    tbl.add_column(T("col_messages"), style=C_MAIN,   width=10, justify="right")
    tbl.add_column(T("col_share"),    style=C_DIM,    width=8,  justify="right")
    tbl.add_column(T("col_dist"),     min_width=BAR_W)
    for tag, count in sorted_data:
        pct = f"{count / total * 100:.1f}%" if total else "0%"
        tbl.add_row(tag, str(count), pct, _bar(count, max_c))
    console.print(tbl)