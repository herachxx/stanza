#!/usr/bin/env python3
"""
stanza - WhatsApp Chat Analyzer
Run:  python main.py menu
      python main.py summary -f chat.txt
"""
from __future__ import annotations
import io
import sys
from datetime import datetime
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_file       # noqa: E402
import analytics as an              # noqa: E402
import display as di                # noqa: E402
from language import T, EN, RU, KZ_C, KZ_L  # noqa: E402
console = Console()
RESULTS_FILE = Path(__file__).parent / "results.txt"
def _select_language() -> None:
    """Ask the user to pick a language. Sets T globally."""
    console.print()
    console.print(Panel(
        f"[bold cyan]stanza[/]  [grey50]WhatsApp Chat Analyzer[/]",
        border_style="cyan", padding=(0, 2), expand=False,
    ))
    console.print()
    tbl = Table(box=None, show_header=False, padding=(0, 2))
    tbl.add_column("key", style="bold cyan", width=4)
    tbl.add_column("lang", style="white")
    tbl.add_row("1", "English")
    tbl.add_row("2", "Русский")
    tbl.add_row("3", "Қазақша / Qazaqsha")
    console.print(tbl)
    console.print()
    while True:
        choice = Prompt.ask("[cyan]Language / Язык / Тіл[/]", default="1").strip()
        if choice == "1":
            T.set_lang(EN)
            return
        elif choice == "2":
            T.set_lang(RU)
            return
        elif choice == "3":
            console.print()
            tbl2 = Table(box=None, show_header=False, padding=(0, 2))
            tbl2.add_column("key", style="bold cyan", width=4)
            tbl2.add_column("script", style="white")
            tbl2.add_row("1", "Қазақша  (кирилл / Cyrillic)")
            tbl2.add_row("2", "Qazaqsha (latyn / Latin)")
            console.print(tbl2)
            console.print()
            sc = Prompt.ask("[cyan]Жазу / Script[/]", default="1").strip()
            T.set_lang(KZ_C if sc != "2" else KZ_L)
            return
        console.print("[red]1 / 2 / 3[/]")
def _save_to_file(label: str, chat_path: str, render_fn, *args, **kwargs) -> None:
    """Render to terminal, then re-render without color and append to results.txt."""
    render_fn(*args, **kwargs)
    buf = io.StringIO()
    file_con = Console(file=buf, highlight=False, markup=True, no_color=True, width=100)
    orig = di.console
    di.console = file_con
    try:
        render_fn(*args, **kwargs)
    finally:
        di.console = orig
    ts = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    header = (
        f"\n{'=' * 100}\n"
        f"[{ts}]  {label}  |  {T('file_label')}: {chat_path}\n"
        f"{'=' * 100}\n"
    )
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(header)
        f.write(buf.getvalue())
        f.write("\n")
def _clear_results() -> None:
    if RESULTS_FILE.exists() and RESULTS_FILE.stat().st_size > 0:
        if Confirm.ask(f"[yellow]{T('clear_confirm')}[/]"):
            RESULTS_FILE.write_text("", encoding="utf-8")
            console.print(f"[green]✓ {T('clear_done')}[/]\n")
    else:
        console.print(f"[grey50]{T('clear_already_empty')}[/]\n")
def _load(path: str):
    console.print(f"[grey50]{T('parsing')} {path} ...[/]")
    msgs = parse_file(path)
    um = an.user_messages(msgs)
    console.print(
        f"[grey50]{T('loaded', total=len(msgs), user=len(um), system=len(msgs) - len(um))}[/]\n"
    )
    return msgs
def _pick_chat_file() -> str | None:
    folder = Path(__file__).parent
    txt_files = sorted(f for f in folder.glob("*.txt") if f.name != "results.txt")
    console.print()
    if txt_files:
        tbl = Table(box=box.SIMPLE, show_header=True,
                    header_style="bold white", border_style="grey50")
        tbl.add_column("#",                style="grey50",       width=4,  justify="right")
        tbl.add_column(T("file_col"),      style="bright_yellow")
        tbl.add_column(T("size_col"),      style="grey50",                 justify="right")
        for i, f in enumerate(txt_files, 1):
            tbl.add_row(str(i), f.name, f"{f.stat().st_size // 1024} KB")
        console.print(Panel(tbl, title=f"[bold cyan]{T('found_files_title')}[/]",
                            border_style="cyan", padding=(0, 1)))
        console.print(f"[grey50]{T('file_picker_hint')}[/]\n")
        choice = Prompt.ask(f"[cyan]{T('file_prompt')}[/]", default="chat.txt").strip()
    else:
        console.print(f"[grey50]{T('file_picker_no_files')}[/]")
        choice = Prompt.ask(f"[cyan]{T('file_path_prompt')}[/]").strip()
    if choice.isdigit() and txt_files:
        idx = int(choice) - 1
        if 0 <= idx < len(txt_files):
            return str(txt_files[idx])
        console.print(f"[red]{T('invalid_number')}[/]")
        return None
    p = Path(choice)
    if not p.exists():
        console.print(f"[red]{T('file_not_found')}: {choice}[/]")
        return None
    return str(p)
MENU_KEYS = [
    ("1", "menu_summary",     "summary"),
    ("2", "menu_users",       "users"),
    ("3", "menu_activity",    "activity"),
    ("4", "menu_graph",       "graph"),
    ("5", "menu_topics",      "topics"),
    ("6", "menu_media",       "media"),
    ("7", "menu_ghosts",      "ghosts"),
    ("8", "menu_penalties",   "penalties"),
    ("a", "menu_all",         "all"),
    ("d", "menu_digest",      "digest"),
    ("-", None,               None),
    ("s", "menu_save_toggle", "_save_toggle"),
    ("c", "menu_clear",       "_clear"),
    ("f", "menu_change_file", "_change_file"),
    ("q", "menu_quit",        "_quit"),
]
def _print_menu(chat_path: str, save_enabled: bool) -> None:
    save_str = (
        f"[green]{T('saving_on')}[/]"
        if save_enabled
        else f"[grey50]{T('saving_off')}[/]"
    )
    header = (
        f"[bold cyan]stanza[/]  [grey50]{T('version')}[/]\n"
        f"[grey50]{T('file_label')}:[/]    [bright_yellow]{Path(chat_path).name}[/]\n"
        f"[grey50]{T('saving_label')}:[/]  {save_str}  "
        f"[grey50]({T('results_arrow')})[/]"
    )
    console.print(Panel(header, border_style="cyan", padding=(0, 2)))
    tbl = Table(box=None, show_header=False, padding=(0, 2))
    tbl.add_column("key",  style="bold cyan", width=4)
    tbl.add_column("desc", style="white")
    for key, label_key, _ in MENU_KEYS:
        if key == "-":
            tbl.add_row("", "[grey30]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
        else:
            tbl.add_row(key, T(label_key))
    console.print(tbl)
    console.print()
def _run_analysis(cmd: str, msgs, chat_path: str, save: bool) -> None:
    TOP = 15
    def _do(label_key: str, fn, *args, **kwargs):
        console.rule(f"[bold cyan]{T(label_key)}[/]")
        if save:
            _save_to_file(T(label_key), chat_path, fn, *args, **kwargs)
        else:
            fn(*args, **kwargs)
    if cmd == "summary":
        _do("section_summary", di.render_summary, an.compute_stats(msgs))
    elif cmd == "users":
        _do("section_users", di.render_top_users, an.top_users(msgs, n=TOP))
    elif cmd == "activity":
        _do("title_hourly",  di.render_hourly_activity,  an.activity_by_hour(msgs))
        _do("title_weekday", di.render_weekday_activity, an.activity_by_weekday(msgs))
        _do("title_daily",   di.render_daily_activity,   an.activity_by_date(msgs))
    elif cmd == "graph":
        _do("section_graph", di.render_interaction_graph,
            an.top_interactions(msgs, n=TOP))
    elif cmd == "topics":
        _do("title_topics", di.render_topics,     an.topic_distribution(msgs))
        _do("title_tech",   di.render_tech_stack, an.extract_tech_stack(msgs))
    elif cmd == "media":
        _do("section_media", di.render_media, an.media_by_user(msgs)[:TOP])
    elif cmd == "ghosts":
        _do("section_ghosts", di.render_ghosts, an.ghost_participants(msgs))
    elif cmd == "penalties":
        _do("section_penalties", di.render_penalties, an.extract_penalties(msgs))
    elif cmd == "all":
        steps = [
            ("section_summary",   di.render_summary,           (an.compute_stats(msgs),)),
            ("section_users",     di.render_top_users,         (an.top_users(msgs, n=TOP),)),
            ("title_hourly",      di.render_hourly_activity,   (an.activity_by_hour(msgs),)),
            ("title_weekday",     di.render_weekday_activity,  (an.activity_by_weekday(msgs),)),
            ("title_daily",       di.render_daily_activity,    (an.activity_by_date(msgs),)),
            ("section_graph",     di.render_interaction_graph, (an.top_interactions(msgs, n=TOP),)),
            ("title_topics",      di.render_topics,            (an.topic_distribution(msgs),)),
            ("title_tech",        di.render_tech_stack,        (an.extract_tech_stack(msgs),)),
            ("section_media",     di.render_media,             (an.media_by_user(msgs)[:TOP],)),
            ("section_ghosts",    di.render_ghosts,            (an.ghost_participants(msgs),)),
            ("section_penalties", di.render_penalties,         (an.extract_penalties(msgs),)),
        ]
        for lk, fn, args in steps:
            _do(lk, fn, *args)
        console.print(f"\n[bold green]✓ {T('all_done')}[/]")
        if save:
            console.print(f"[grey50]{T('results_saved')}[/]")
    elif cmd == "digest":
        from digest import generate_digest
        raw = Prompt.ask(
            f"[cyan]{T('digest_date_prompt')}[/]", default=""
        ).strip()
        days = None
        if raw:
            try:
                days = [datetime.strptime(raw, "%Y-%m-%d").date()]
            except ValueError:
                console.print(f"[red]{T('digest_bad_date')}[/]")
                return
        generate_digest(msgs, days=days)
@click.group()
@click.version_option("1.0.0", prog_name="stanza")
def cli():
    """WhatsApp chat analytics tool - stanza."""
    pass
@cli.command()
def menu():
    """Interactive menu (recommended)."""
    console.clear()
    _select_language()
    console.clear()
    chat_path = _pick_chat_file()
    if not chat_path:
        console.print(f"[red]{T('no_file_selected')}[/]")
        return
    msgs = _load(chat_path)
    save_enabled = False
    while True:
        console.print()
        _print_menu(chat_path, save_enabled)
        choice = Prompt.ask(f"[cyan]{T('choose_action')}[/]").strip().lower()
        console.print()
        cmd = None
        for key, _, action in MENU_KEYS:
            if key == choice:
                cmd = action
                break
        if cmd is None:
            console.print(f"[red]{T('invalid_choice')}[/]")
            continue
        if cmd == "_quit":
            console.print(f"[grey50]{T('exit_msg')}[/]")
            break
        elif cmd == "_clear":
            _clear_results()
        elif cmd == "_change_file":
            new_path = _pick_chat_file()
            if new_path:
                chat_path = new_path
                msgs = _load(chat_path)
                console.print(f"[green]✓ {T('loaded_label')}:[/] {Path(chat_path).name}\n")
        elif cmd == "_save_toggle":
            save_enabled = not save_enabled
            msg = T("save_enabled") if save_enabled else T("save_disabled")
            console.print(f"[{'green' if save_enabled else 'grey50'}]{msg}[/]\n")
        else:
            _run_analysis(cmd, msgs, chat_path, save_enabled)
        input(T("press_enter"))
        console.clear()
_file_opt = click.option("--file", "-f", default="chat.txt", show_default=True,
                         type=click.Path(exists=True, dir_okay=False, readable=True))
_save_opt = click.option("--save/--no-save", "-s", default=False)
_lang_opt = click.option("--lang", "-l",
                         type=click.Choice(["en", "ru", "kz_c", "kz_l"], case_sensitive=False),
                         default="en", show_default=True, help="Language / Язык")
def _set_lang(lang: str) -> None:
    T.set_lang({"en": EN, "ru": RU, "kz_c": KZ_C, "kz_l": KZ_L}.get(lang.lower(), EN))
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
def summary(file, save, lang):
    """Chat overview."""
    _set_lang(lang); msgs = _load(file)
    if save: _save_to_file(T("section_summary"), file, di.render_summary, an.compute_stats(msgs))
    else: di.render_summary(an.compute_stats(msgs))
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
@click.option("--top", "-n", default=20, show_default=True)
def users(file, save, lang, top):
    """Top users."""
    _set_lang(lang); msgs = _load(file)
    data = an.top_users(msgs, n=top)
    if save: _save_to_file(T("section_users"), file, di.render_top_users, data)
    else: di.render_top_users(data)
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
@click.option("--mode", "-m",
              type=click.Choice(["hour", "weekday", "date", "all"], case_sensitive=False),
              default="all", show_default=True)
def activity(file, save, lang, mode):
    """Activity over time."""
    _set_lang(lang); msgs = _load(file); mode = mode.lower()
    pairs = []
    if mode in ("hour", "all"):    pairs.append(("title_hourly",  di.render_hourly_activity,  an.activity_by_hour(msgs)))
    if mode in ("weekday", "all"): pairs.append(("title_weekday", di.render_weekday_activity, an.activity_by_weekday(msgs)))
    if mode in ("date", "all"):    pairs.append(("title_daily",   di.render_daily_activity,   an.activity_by_date(msgs)))
    for lk, fn, data in pairs:
        if save: _save_to_file(T(lk), file, fn, data)
        else: fn(data)
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
@click.option("--top", "-n", default=15, show_default=True)
@click.option("--window", "-w", default=120, show_default=True)
def graph(file, save, lang, top, window):
    """Interaction graph."""
    _set_lang(lang); msgs = _load(file)
    edges = an.top_interactions(msgs, n=top, window_seconds=window)
    if save: _save_to_file(T("section_graph"), file, di.render_interaction_graph, edges, top_n=top)
    else: di.render_interaction_graph(edges, top_n=top)
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
@click.option("--show-tech/--no-tech", default=True)
def topics(file, save, lang, show_tech):
    """Topics & tech stack."""
    _set_lang(lang); msgs = _load(file)
    if save:
        _save_to_file(T("title_topics"), file, di.render_topics, an.topic_distribution(msgs))
        if show_tech: _save_to_file(T("title_tech"), file, di.render_tech_stack, an.extract_tech_stack(msgs))
    else:
        di.render_topics(an.topic_distribution(msgs))
        if show_tech: console.print(); di.render_tech_stack(an.extract_tech_stack(msgs))
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
@click.option("--top", "-n", default=15, show_default=True)
def media(file, save, lang, top):
    """Media files."""
    _set_lang(lang); msgs = _load(file)
    data = an.media_by_user(msgs)[:top]
    if save: _save_to_file(T("section_media"), file, di.render_media, data)
    else: di.render_media(data)
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
def ghosts(file, save, lang):
    """Silent members."""
    _set_lang(lang); msgs = _load(file)
    gl = an.ghost_participants(msgs)
    if save: _save_to_file(T("section_ghosts"), file, di.render_ghosts, gl)
    else: di.render_ghosts(gl)
@cli.command()
@_file_opt
@_save_opt
@_lang_opt
def penalties(file, save, lang):
    """Penalty events."""
    _set_lang(lang); msgs = _load(file)
    evs = an.extract_penalties(msgs)
    if save: _save_to_file(T("section_penalties"), file, di.render_penalties, evs)
    else: di.render_penalties(evs)
@cli.command()
@_file_opt
@_lang_opt
@click.option("--date", "-d", "target_date", default=None,
              help="YYYY-MM-DD, or omit for all dates.")
def digest(file, lang, target_date):
    """AI daily digest. Requires ANTHROPIC_API_KEY."""
    from digest import generate_digest
    _set_lang(lang); msgs = _load(file)
    days = None
    if target_date:
        try:
            days = [datetime.strptime(target_date, "%Y-%m-%d").date()]
        except ValueError:
            raise click.BadParameter("Use YYYY-MM-DD")
    generate_digest(msgs, days=days)
@cli.command(name="all")
@_file_opt
@_save_opt
@_lang_opt
@click.option("--top", "-n", default=15, show_default=True)
def run_all(file, save, lang, top):
    """Run all analyses."""
    _set_lang(lang); msgs = _load(file)
    _run_analysis("all", msgs, file, save)
@cli.command(name="clear")
def clear_cmd():
    """Clear results.txt."""
    _clear_results()
@cli.command(name="web")
@click.option("--port", "-p", default=5000, show_default=True, help="Port to listen on.")
@click.option("--no-browser", is_flag=True, default=False, help="Don't open browser automatically.")
def web_cmd(port: int, no_browser: bool):
    """Launch the web dashboard."""
    from web import run as web_run
    web_run(port=port, open_browser=not no_browser)
if __name__ == "__main__":
    cli()