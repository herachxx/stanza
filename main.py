#!/usr/bin/env python3
"""
chat-analyzer - WhatsApp chat log analytics CLI
Запуск через меню:  python main.py menu
Или напрямую:       python main.py summary -f chat.txt
"""
from __future__ import annotations
import sys
from datetime import date, datetime
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box
sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_file  # noqa: E402
import analytics as an          # noqa: E402
import display as di            # noqa: E402
console = Console()
RESULTS_FILE = Path(__file__).parent / "results.txt"
def _save_to_file(label: str, chat_path: str, render_fn, *args, **kwargs) -> None:
    import io
    from rich.console import Console as RichConsole
    render_fn(*args, **kwargs)
    string_buf = io.StringIO()
    file_console = RichConsole(
        file=string_buf, highlight=False, markup=True,
        no_color=True, width=100
    )
    orig = di.console
    di.console = file_console
    try:
        render_fn(*args, **kwargs)
    finally:
        di.console = orig
    plain_text = string_buf.getvalue()
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    header = (
        f"\n{'=' * 100}\n"
        f"[{timestamp}]  {label}  |  файл: {chat_path}\n"
        f"{'=' * 100}\n"
    )
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(header)
        f.write(plain_text)
        f.write("\n")
def _clear_results() -> None:
    if RESULTS_FILE.exists() and RESULTS_FILE.stat().st_size > 0:
        if Confirm.ask(
            f"[yellow]Очистить[/] {RESULTS_FILE.name}? Это удалит все сохранённые результаты"
        ):
            RESULTS_FILE.write_text("", encoding="utf-8")
            console.print("[green]✓ Файл results.txt очищен.[/]\n")
    else:
        console.print("[grey50]Файл results.txt уже пуст или не существует.[/]\n")
def _load(path: str):
    console.print(f"[grey50]Парсинг {path} …[/]")
    msgs = parse_file(path)
    um = an.user_messages(msgs)
    console.print(
        f"[grey50]Загружено {len(msgs)} сообщений "
        f"({len(um)} пользовательских, {len(msgs) - len(um)} системных)[/]\n"
    )
    return msgs
def _pick_chat_file() -> str | None:
    """
    Показывает список .txt файлов в папке проекта.
    Пользователь вводит номер или полный путь.
    """
    folder = Path(__file__).parent
    txt_files = sorted(f for f in folder.glob("*.txt") if f.name != "results.txt")
    console.print()
    if txt_files:
        table = Table(
            box=box.SIMPLE, show_header=True,
            header_style="bold white", border_style="grey50"
        )
        table.add_column("#", style="grey50", width=4, justify="right")
        table.add_column("Файл", style="bright_yellow")
        table.add_column("Размер", style="grey50", justify="right")
        for i, f in enumerate(txt_files, 1):
            size_kb = f.stat().st_size // 1024
            table.add_row(str(i), f.name, f"{size_kb} KB")
        console.print(Panel(
            table,
            title="[bold cyan]Найденные .txt файлы в папке[/]",
            border_style="cyan", padding=(0, 1)
        ))
        console.print("[grey50]Введи номер, или полный путь к другому файлу, или Enter для chat.txt[/]\n")
        choice = Prompt.ask("[cyan]Файл чата[/]", default="chat.txt").strip()
    else:
        console.print("[grey50]В папке не найдены .txt файлы. Укажи путь вручную:[/]")
        choice = Prompt.ask("[cyan]Путь к файлу чата[/]").strip()
    if choice.isdigit() and txt_files:
        idx = int(choice) - 1
        if 0 <= idx < len(txt_files):
            return str(txt_files[idx])
        console.print("[red]Неверный номер.[/]")
        return None
    p = Path(choice)
    if not p.exists():
        console.print(f"[red]Файл не найден: {choice}[/]")
        return None
    return str(p)
_file_option = click.option(
    '--file', '-f',
    default='chat.txt',
    show_default=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help='Путь к экспорту WhatsApp (.txt).',
)
_save_option = click.option(
    '--save/--no-save', '-s',
    default=False,
    help='Сохранить результат в results.txt.',
)
MENU_ITEMS = [
    ("1", "Обзор чата",              "summary"),
    ("2", "Топ пользователей",       "users"),
    ("3", "Активность по времени",   "activity"),
    ("4", "Граф взаимодействий",     "graph"),
    ("5", "Темы и технологии",       "topics"),
    ("6", "Медиафайлы",              "media"),
    ("7", "Молчуны (ghosts)",        "ghosts"),
    ("8", "Штрафные баллы",          "penalties"),
    ("9", "Запустить всё",           "all"),
    ("d", "AI-дайджест по дням",     "digest"),
    ("━", None,                      None),
    ("s", "Включить/выключить сохранение в results.txt", "_save_toggle"),
    ("c", "Очистить results.txt",    "_clear"),
    ("f", "Сменить файл чата",       "_change_file"),
    ("q", "Выход",                   "_quit"),
]
def _print_menu(chat_path: str, save_enabled: bool) -> None:
    save_status = "[green]ВКЛ ✓[/]" if save_enabled else "[grey50]ВЫКЛ[/]"
    header = (
        f"[bold cyan]chat-analyzer[/]  v1.0\n"
        f"[grey50]Файл:[/]       [bright_yellow]{Path(chat_path).name}[/]\n"
        f"[grey50]Сохранение:[/] {save_status}  [grey50](результаты → results.txt)[/]"
    )
    console.print(Panel(header, border_style="cyan", padding=(0, 2)))
    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column("key", style="bold cyan", width=4)
    table.add_column("desc", style="white")
    for key, desc, _ in MENU_ITEMS:
        if key == "━":
            table.add_row("", "[grey30]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]")
        else:
            table.add_row(key, desc)
    console.print(table)
    console.print()
def _run_analysis(cmd: str, msgs, chat_path: str, save: bool) -> None:
    """Запускает нужный анализ. При save=True дублирует результат в файл."""
    top = 15
    def _do(label: str, fn, *args, **kwargs):
        console.rule(f"[bold cyan]{label}[/]")
        if save:
            _save_to_file(label, chat_path, fn, *args, **kwargs)
        else:
            fn(*args, **kwargs)
    if cmd == "summary":
        _do("Обзор чата", di.render_summary, an.compute_stats(msgs))
    elif cmd == "users":
        _do("Топ пользователей", di.render_top_users, an.top_users(msgs, n=top))
    elif cmd == "activity":
        _do("Активность по часам",     di.render_hourly_activity,  an.activity_by_hour(msgs))
        _do("Активность по дням нед.", di.render_weekday_activity, an.activity_by_weekday(msgs))
        _do("Активность по датам",     di.render_daily_activity,   an.activity_by_date(msgs))
    elif cmd == "graph":
        _do("Граф взаимодействий", di.render_interaction_graph,
            an.top_interactions(msgs, n=top))
    elif cmd == "topics":
        _do("Темы сообщений",  di.render_topics,     an.topic_distribution(msgs))
        _do("Стек технологий", di.render_tech_stack, an.extract_tech_stack(msgs))
    elif cmd == "media":
        _do("Медиафайлы", di.render_media, an.media_by_user(msgs)[:top])
    elif cmd == "ghosts":
        _do("Молчуны", di.render_ghosts, an.ghost_participants(msgs))
    elif cmd == "penalties":
        _do("Штрафные баллы", di.render_penalties, an.extract_penalties(msgs))
    elif cmd == "all":
        steps = [
            ("Обзор чата",              di.render_summary,           (an.compute_stats(msgs),),         {}),
            ("Топ пользователей",       di.render_top_users,         (an.top_users(msgs, n=top),),      {}),
            ("Активность по часам",     di.render_hourly_activity,   (an.activity_by_hour(msgs),),      {}),
            ("Активность по дням нед.", di.render_weekday_activity,  (an.activity_by_weekday(msgs),),   {}),
            ("Активность по датам",     di.render_daily_activity,    (an.activity_by_date(msgs),),      {}),
            ("Граф взаимодействий",     di.render_interaction_graph, (an.top_interactions(msgs, n=top),), {}),
            ("Темы сообщений",          di.render_topics,            (an.topic_distribution(msgs),),    {}),
            ("Стек технологий",         di.render_tech_stack,        (an.extract_tech_stack(msgs),),    {}),
            ("Медиафайлы",              di.render_media,             (an.media_by_user(msgs)[:top],),   {}),
            ("Молчуны",                 di.render_ghosts,            (an.ghost_participants(msgs),),    {}),
            ("Штрафные баллы",          di.render_penalties,         (an.extract_penalties(msgs),),     {}),
        ]
        for label, fn, args, kwargs in steps:
            _do(label, fn, *args, **kwargs)
        console.print("\n[bold green]✓ Все анализы выполнены.[/]")
        if save:
            console.print(f"[grey50]Результаты сохранены → [bold]{RESULTS_FILE.name}[/][/]")
    elif cmd == "digest":
        from digest import generate_digest
        raw = Prompt.ask(
            "[cyan]Дата для дайджеста[/] [grey50](YYYY-MM-DD, или Enter для всех дат)[/]",
            default=""
        ).strip()
        days = None
        if raw:
            try:
                days = [datetime.strptime(raw, "%Y-%m-%d").date()]
            except ValueError:
                console.print("[red]Неверный формат. Используй YYYY-MM-DD[/]")
                return
        generate_digest(msgs, days=days)
@click.group()
@click.version_option('1.0.0', prog_name='chat-analyzer')
def cli():
    """WhatsApp chat log analytics tool."""
    pass
@cli.command()
def menu():
    """Интерактивное меню - рекомендуемый способ запуска."""
    console.clear()
    chat_path = _pick_chat_file()
    if not chat_path:
        console.print("[red]Файл не выбран. Выход.[/]")
        return
    msgs = _load(chat_path)
    save_enabled = False
    while True:
        console.print()
        _print_menu(chat_path, save_enabled)
        choice = Prompt.ask("[cyan]Выбери действие[/]").strip().lower()
        console.print()
        cmd = None
        for key, _, action in MENU_ITEMS:
            if key == choice:
                cmd = action
                break
        if cmd is None:
            console.print("[red]Неверный выбор. Попробуй снова.[/]")
            continue
        if cmd == "_quit":
            console.print("[grey50]Выход.[/]")
            break
        elif cmd == "_clear":
            _clear_results()
        elif cmd == "_change_file":
            new_path = _pick_chat_file()
            if new_path:
                chat_path = new_path
                msgs = _load(chat_path)
                console.print(f"[green]✓ Загружен:[/] {Path(chat_path).name}\n")
        elif cmd == "_save_toggle":
            save_enabled = not save_enabled
            state = "[green]включено ✓[/]" if save_enabled else "[grey50]выключено[/]"
            console.print(f"Сохранение в results.txt: {state}\n")
        else:
            _run_analysis(cmd, msgs, chat_path, save_enabled)
        input("\n  Нажми Enter чтобы вернуться в меню…")
        console.clear()
@cli.command()
@_file_option
@_save_option
def summary(file: str, save: bool):
    """Обзор чата."""
    msgs = _load(file)
    if save:
        _save_to_file("Обзор чата", file, di.render_summary, an.compute_stats(msgs))
    else:
        di.render_summary(an.compute_stats(msgs))
@cli.command()
@_file_option
@_save_option
@click.option('--top', '-n', default=20, show_default=True)
def users(file: str, save: bool, top: int):
    """Топ пользователей."""
    msgs = _load(file)
    data = an.top_users(msgs, n=top)
    if save:
        _save_to_file("Топ пользователей", file, di.render_top_users, data)
    else:
        di.render_top_users(data)
@cli.command()
@_file_option
@_save_option
@click.option(
    '--mode', '-m',
    type=click.Choice(['hour', 'weekday', 'date', 'all'], case_sensitive=False),
    default='all', show_default=True
)
def activity(file: str, save: bool, mode: str):
    """Активность по времени."""
    msgs = _load(file)
    mode = mode.lower()
    pairs = []
    if mode in ('hour', 'all'):
        pairs.append(("Активность по часам", di.render_hourly_activity, an.activity_by_hour(msgs)))
    if mode in ('weekday', 'all'):
        pairs.append(("Активность по дням", di.render_weekday_activity, an.activity_by_weekday(msgs)))
    if mode in ('date', 'all'):
        pairs.append(("Активность по датам", di.render_daily_activity, an.activity_by_date(msgs)))
    for label, fn, data in pairs:
        if save:
            _save_to_file(label, file, fn, data)
        else:
            fn(data)
@cli.command()
@_file_option
@_save_option
@click.option('--top', '-n', default=15, show_default=True)
@click.option('--window', '-w', default=120, show_default=True)
def graph(file: str, save: bool, top: int, window: int):
    """Граф взаимодействий."""
    msgs = _load(file)
    edges = an.top_interactions(msgs, n=top, window_seconds=window)
    if save:
        _save_to_file("Граф взаимодействий", file, di.render_interaction_graph, edges, top_n=top)
    else:
        di.render_interaction_graph(edges, top_n=top)
@cli.command()
@_file_option
@_save_option
@click.option('--show-tech/--no-tech', default=True)
def topics(file: str, save: bool, show_tech: bool):
    """Темы и технологии."""
    msgs = _load(file)
    if save:
        _save_to_file("Темы", file, di.render_topics, an.topic_distribution(msgs))
        if show_tech:
            _save_to_file("Стек технологий", file, di.render_tech_stack, an.extract_tech_stack(msgs))
    else:
        di.render_topics(an.topic_distribution(msgs))
        if show_tech:
            console.print()
            di.render_tech_stack(an.extract_tech_stack(msgs))
@cli.command()
@_file_option
@_save_option
@click.option('--top', '-n', default=15, show_default=True)
def media(file: str, save: bool, top: int):
    """Медиафайлы."""
    msgs = _load(file)
    data = an.media_by_user(msgs)[:top]
    if save:
        _save_to_file("Медиафайлы", file, di.render_media, data)
    else:
        di.render_media(data)
@cli.command()
@_file_option
@_save_option
def ghosts(file: str, save: bool):
    """Молчуны."""
    msgs = _load(file)
    ghost_list = an.ghost_participants(msgs)
    if save:
        _save_to_file("Молчуны", file, di.render_ghosts, ghost_list)
    else:
        di.render_ghosts(ghost_list)
@cli.command()
@_file_option
@_save_option
def penalties(file: str, save: bool):
    """Штрафные баллы."""
    msgs = _load(file)
    events = an.extract_penalties(msgs)
    if save:
        _save_to_file("Штрафные баллы", file, di.render_penalties, events)
    else:
        di.render_penalties(events)
@cli.command()
@_file_option
@click.option('--date', '-d', 'target_date', default=None,
              help='Дата в формате YYYY-MM-DD. По умолчанию - все дни.')
def digest(file: str, target_date: str | None):
    """AI-дайджест. Требует ANTHROPIC_API_KEY."""
    from digest import generate_digest
    msgs = _load(file)
    days = None
    if target_date:
        try:
            days = [datetime.strptime(target_date, '%Y-%m-%d').date()]
        except ValueError:
            raise click.BadParameter("Формат: YYYY-MM-DD")
    generate_digest(msgs, days=days)
@cli.command(name='all')
@_file_option
@_save_option
@click.option('--top', '-n', default=15, show_default=True)
def run_all(file: str, save: bool, top: int):
    """Запустить все анализы."""
    msgs = _load(file)
    _run_analysis("all", msgs, file, save)
@cli.command(name='clear')
def clear_cmd():
    """Очистить файл results.txt."""
    _clear_results()
if __name__ == '__main__':
    cli()