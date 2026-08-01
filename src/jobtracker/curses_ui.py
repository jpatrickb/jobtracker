"""Arrow-key select menus for `jobtracker setup` (see wizard.py), built on stdlib `curses` so no
new dependency is needed for something this small.

Falls back to a numbered list read over plain stdin when there's no real terminal to draw a
curses menu on -- piped/redirected input, exactly how an agent or a CI script invokes this
command -- mirroring the interactivity check in store.py's `_is_interactive()`. The fallback path
is a separate, directly-callable function so it can be exercised without a real pty, e.g.:

    printf '2\\n' | python -c "
from rich.console import Console
from jobtracker.curses_ui import _fallback_choice
print(_fallback_choice(Console(), 'Pick one', ['annual', 'hourly'], 0))
"
"""
import curses
import sys

from rich.prompt import Prompt


def _is_interactive():
    """True only when both ends are a real terminal -- see store._is_interactive() for the same
    reasoning: never block an automated/piped invocation waiting on a menu it has no way to
    render or drive."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _curses_menu(stdscr, question, choices, default_index):
    """The curses render/input loop, run inside curses.wrapper() (which handles terminal
    setup/teardown, including restoring the terminal on any exception). Returns the index of the
    chosen option. Escape resolves to `default_index`, same as a bare Enter -- there's no separate
    "cancelled" state for these call sites, every one of them already has a sensible default to
    fall back to."""
    curses.curs_set(0)
    selected = default_index

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        def put(y, text, attr=0):
            if 0 <= y < max_y:
                stdscr.addstr(y, 0, text[: max(max_x - 1, 0)], attr)

        put(0, question)
        put(1, "(Up/Down to move, Enter to select, Esc for default)")
        for i, choice in enumerate(choices):
            label = f"{'>' if i == selected else ' '} {choice}"
            put(3 + i, label, curses.A_REVERSE if i == selected else 0)
        stdscr.refresh()

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord("k")):
            selected = (selected - 1) % len(choices)
        elif key in (curses.KEY_DOWN, ord("j")):
            selected = (selected + 1) % len(choices)
        elif key in (curses.KEY_ENTER, 10, 13):
            return selected
        elif key == 27:  # Esc
            return default_index


def _fallback_choice(console, question, choices, default_index):
    """Numbered-list fallback for when curses/a real TTY isn't available. Reads a single line
    from stdin via rich's Prompt (the same way every other wizard prompt reads input), so it
    behaves the same whether stdin is a pty or a pipe. Bare Enter resolves to the default -- there
    is no distinct "Escape" on a plain stream, so accepting the default is how cancel/skip is
    expressed here too."""
    console.print(f"\n{question}")
    for i, choice in enumerate(choices, 1):
        suffix = "  (default)" if i - 1 == default_index else ""
        console.print(f"  {i}. {choice}{suffix}")

    numbers = [str(i) for i in range(1, len(choices) + 1)]
    raw = Prompt.ask(
        "Enter a number",
        choices=numbers,
        default=numbers[default_index],
        show_choices=False,
        console=console,
    )
    return choices[int(raw) - 1]


def prompt_choice(console, question, choices, default):
    """Ask the user to pick one of `choices` (a list of short strings) for `question`.

    Renders an arrow-key radio-list menu when stdin/stdout are both a real terminal and curses is
    usable; otherwise falls back to a numbered list read from stdin (see _fallback_choice), so a
    non-interactive/piped invocation -- exactly how an agent runs this command -- never blocks
    waiting on a menu it can't render.

    `default` must be one of `choices`; it's both the option pre-selected in the curses menu and
    what a bare Enter (or Escape) resolves to in either path. Returns the chosen value from
    `choices`.
    """
    if default not in choices:
        raise ValueError(f"default {default!r} is not among choices {choices!r}")
    default_index = choices.index(default)

    if _is_interactive():
        try:
            index = curses.wrapper(_curses_menu, question, choices, default_index)
            return choices[index]
        except Exception:
            # Any curses failure (unsupported TERM, terminal too small, etc.) -- don't crash the
            # wizard over a rendering problem, just fall back to the plain numbered list.
            pass

    return _fallback_choice(console, question, choices, default_index)
