from __future__ import annotations
import time
import threading
from pathlib import Path
from rich.live import Live
from rich.spinner import Spinner
from rich.align import Align
from rich.console import Group
from src.ui.menus import (
    console,
    selection_main_menu, 
    selection_settings,
    ask_file_path,
    ask_image_path,
    input_puzzle_string,
    back_to_menu,
)
from src.algorithms.uniqueness_solver.complete_solver import (
    _parse,
    timeit,
    solve,
    generate_display_grid_string
)
from src.image_parsing.image_parser import (
    parse_sudoku_image,
    show_cell_grid,
    stack_cells,
    _show,
)
from src.ui.settings import settings
from rich.panel import Panel
from rich.text import Text


_LOGO = """
███████╗██╗   ██╗██████╗  ██████╗ ██╗  ██╗██╗   ██╗
██╔════╝██║   ██║██╔══██╗██╔═══██╗██║ ██╔╝██║   ██║
███████╗██║   ██║██║  ██║██║   ██║█████╔╝ ██║   ██║
╚════██║██║   ██║██║  ██║██║   ██║██╔═██╗ ██║   ██║
███████║╚██████╔╝██████╔╝╚██████╔╝██║  ██╗╚██████╔╝
╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 
"""


EXIT_MESSAGE = Panel(
      Text("Goodbye 👋", justify="center"), 
      border_style="grey93",
      padding=(6)
    )


def loading():
    done = threading.Event()

    def _load():
        from src.models.digit_recognition import _READER  # noqa: F401
        done.set()

    thread = threading.Thread(target=_load, daemon=True)
    thread.start()

    logo = Text(_LOGO, style="bold orange4", justify="center")
    spinner = Spinner("dots", style="orange1")

    with Live(console=console, refresh_per_second=12) as live:
        while not done.is_set():
            status = Align(
                Group(spinner, Align(Text(" Initialising…", style="dim"), align="center")),
                align="center",
            )
            live.update(Panel(Group(logo, status), border_style="orange1", subtitle="[dim]v0.1.0[/dim]"))
            time.sleep(0.08)

    thread.join()


def header():
    logo = Text(_LOGO, style="bold orange1", justify="center")
    console.print(Panel(logo, title_align="center", subtitle="[dim]v0.1.0[/dim]", border_style="orange1"))


def gracefully_exit():
    console.clear()
    settings.save_settings()
    console.print(EXIT_MESSAGE)
    time.sleep(0.5)
    console.clear()
    return exit(0)


def main_menu():
    while True:
        console.clear()
        header()
        choice = selection_main_menu()
        
        if choice == "p_string":
                puzzle_string_menu()

        elif choice == "scan":
                image_selection_menu()

        elif choice == "settings":
                settings_menu()
                break

        elif choice == "quit" or choice is None:
                gracefully_exit()


def settings_menu(default = None):
    console.clear()
    header()
    choice = selection_settings(default = default, settings = settings)
    
    if choice in (
        "display_solved_image",
        "save_solved_image",
        "unique_solution",
        "verbose",
        "debug_mode"
    ):
        new_val = not settings[choice]
        settings[choice] = new_val
        settings.save_settings()
        settings_menu(default=choice)

    
    elif choice == "save_file_path":
        new_fp = ask_file_path()
        if new_fp is not None:
            settings[choice] = new_fp
            settings.save_settings()
        settings_menu(choice)
    
    elif choice == "back" or choice is None:
        console.clear()
        return main_menu()


def image_selection_menu(err: bool = False):
    console.clear()
    header()
    image_file = ask_image_path()

    if isinstance(image_file, str):
        try:
            puzzle = image_ocr_loading(image_file)
            puzzle_display(puzzle)
        except:
            return image_selection_menu()
        

    elif image_file is None:
        return None


def image_ocr_loading(image_file: str):
    console.clear()
    header()
    def _perform_ocr(image_file):
        from src.models.digit_recognition import (
            generate_puzzle_from_cells,
            draw_digit_boxes,
            _READER
        )
        debug = settings['debug']
        show_solved_img = settings['display_solved_image']
        parsed_cells, parsed_image = parse_sudoku_image(image_file, debug)
        if show_solved_img or debug:
            _ocr = draw_digit_boxes(grid_img=stack_cells(parsed_image), cells=parsed_cells, debug=debug)
            _show("Detected Digits", _ocr)
        puzzle = generate_puzzle_from_cells(parsed_cells, reader=_READER, debug=debug)
        return puzzle
    
    return _perform_ocr(image_file)




def puzzle_string_menu(err: bool = False):
    console.clear()
    header()
    puzzle_string = input_puzzle_string(err)
    if isinstance(puzzle_string, str):
        try:
            puzzle = _parse(puzzle_string)
            puzzle_display(puzzle, puzzle_string)
            return
        except:
            return puzzle_string_menu(True)

    elif puzzle_string is None:
         return


def puzzle_display(puzzle, puzzle_string = ""):
    console.clear()
    header()
    limit = 2 if settings['unique_solution'] else 1
    debug = settings['debug']
    verbose = settings['verbose']

    (solution, givens, status), elapsed_time = timeit(solve)(puzzle, limit) #type: ignore
    lines = generate_display_grid_string(solution, givens, status, elapsed_time)
    grid_text, summary = lines[:-4], lines[-4:-1]

    display_panel = Panel(
         Text.assemble(
         Text.from_ansi(
            "\n".join(grid_text)
        ),
         Text.from_ansi(
            "\n".join(summary)
         ), justify='center'
        ),
        title="It's Su-Done-Ku!!", 
        padding=(0, 4, 1, 4),
        highlight=True,
        subtitle=None if puzzle_string == "" else "[dim]code: " + puzzle_string + "[/dim]"
    )
    console.print(display_panel)
    back_to_menu()