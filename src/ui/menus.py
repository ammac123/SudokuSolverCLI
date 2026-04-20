import os
import questionary
from src.ui.settings import settings, IMAGE_EXTS, SUDOKU_DIR
from pathlib import Path
from rich.console import Console
from typing import Literal
from questionary import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding import merge_key_bindings

console = Console()

_choices_style = Style([
      ("pointer", "fg:#e0e0e0 bold"),
      ("highlighted", "fg:#e0e0e0")
])

_settings_style = Style([
      ("pointer", "fg:#808080 bold"),
      ("highlighted", "fg:#e0e0e0"),
      ("selected", "noreverse")
])

_puzzle_string_style = Style([
      ("instructions", "fg:#808080"),
])


def _format_descriptions(text: str):
    n = max(console.width - 18, 40)
    if all([len(line) < n for line in text.splitlines()]):
        return text
    new_lines = []
    for l in text.split(sep='\n'):
        new_text = []
        line = l 
        while True:
            if len(line) < n:
                new_text.append(line)
                break
            idx = line.rfind(' ', 0, n)
            if idx == -1:
                new_text.append(line)
                break
            new_text.append(line[:idx])
            line = line[idx:]
        new_lines.extend(new_text)
    return "\n".join(new_lines)


def settings_choices(settings):
    out = [
        questionary.Choice(
            "Display solved image",
            value="display_solved_image", 
            description=_format_descriptions(
                f"Display the sudoku image in a window after solving. \n  Current: {'Enabled' if settings['display_solved_image'] else 'Disabled'}"
            )
        ),
        questionary.Choice(
            "Check for unique solution",
            value="unique_solution",
            description=_format_descriptions(
                f"Algorithm will check if there a unique solution, otherwise will return first one found. \n  Current: {'Enabled' if settings['unique_solution'] else 'Disabled'}"
            )
        ),
        questionary.Choice(
            "Save processed image to file",
            value="save_solved_image",
            description=f"Save processed sudoku puzzle image to directory in 'Save file path'. \n  Current: {'Enabled' if settings['save_solved_image'] else 'Disabled'}"
        ),
        questionary.Choice(
            "Save file path",
            value="save_file_path",
            description=_format_descriptions(
                f"File path to save images to. \n  Current: \"{settings['save_file_path']}\""
            )
        ),
        questionary.Choice(
            "Verbose",
            value="verbose",
            description=_format_descriptions(
                f"Enable/Disable verbose outputs. \n  Current: {'Enabled' if settings['verbose'] else 'Disabled'}"
            )
        ),
        questionary.Choice(
            "Debug mode",
            value="debug", 
            description=_format_descriptions(
                f"Enable/Disable debug mode. \n  Current: {'Enabled' if settings['debug'] else 'Disabled'}"
            )
        ),
        questionary.Separator(line=
        "───────────────"
        ),
        questionary.Choice(
            "Back",
            value="back"
        )
    ]
    return out


def selection_main_menu() -> Literal["p_string", "scan", "settings", "quit", None]:
    q = questionary.select(
        "Main Menu",
        qmark="",
        choices = [
            questionary.Choice(
            "Input puzzle string", 
                value="p_string", 
                description="Input a sudoku puzzle as text for me to solve."
            ),
            questionary.Choice(
            "Scan image", 
                value="scan",
                description="Select an image of a sudoku on your computer for me try and solve."
            ),
            questionary.Choice(
            "Settings",
                value="settings",
                description="View and change settings."

            ),
            questionary.Separator(line=
            "───────────────"
            ),
            questionary.Choice(
            "Quit",
                value="quit"
            ),
        ],
        show_selected = False,
        use_arrow_keys = True,
        use_shortcuts = True,
        style = _choices_style,
        pointer = " >",
    )
    return q.ask()


def selection_settings(default = None, settings = settings):
    q = questionary.select(
        "Settings",
        choices = settings_choices(settings),
        default = default,
        show_selected = False,
        use_arrow_keys = True,
        use_shortcuts = True,
        style = _settings_style,
        pointer = " >",
    )
    return q.ask()


def ask_file_path():
    def validator(fp):
        try:
            return Path(fp).exists()
        except:
            return False

    bindings = KeyBindings()

    @bindings.add("escape", eager=True)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    q = questionary.path(
        "Choose directory to save or ESC to exit:\n  ",
        default=settings['save_file_path'],
        validate=validator,
        only_directories=True,
    )
    q.application.key_bindings = merge_key_bindings(
      [q.application.key_bindings, bindings] #type: ignore
    )
    try:
        result = q.unsafe_ask()
    except KeyboardInterrupt:
        return
    return result


def ask_image_path():
    def path_filter(path: str):
        if Path(path).suffix.lower() in IMAGE_EXTS:
            return True
        if Path(path).is_dir():
            return True
        return False
    
    def validator(path: str):
        if Path(path).is_file() and path_filter(path):
            return True
        return False
    bindings = KeyBindings()
    @bindings.add("escape", eager=True)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    q = questionary.path(
        "Choose image to open or ESC to exit:\n  ",
        default=Path.home().__str__(),
        validate=validator,
        file_filter=path_filter,
    )
    q.application.key_bindings = merge_key_bindings(
      [q.application.key_bindings, bindings] #type: ignore
    )
    try:
        result = q.unsafe_ask()
    except KeyboardInterrupt:
        return
    return result


def input_puzzle_string(err: bool = False):
    def validator(text):
        if len(text) > 81:
            return False
        if any([t not in ".1234567890" for t in text]):
            return False
        return True
    bindings = KeyBindings()
    @bindings.add("escape", eager=True)
    def _(event):
        event.app.exit(exception=KeyboardInterrupt)

    instructions = _format_descriptions("A Sudoku puzzle string is an 81 characters long, with the first row being the first 9 characters, second row being the next 9, and so on. Empty spaces are represented with either a '.' or '0'.") + '\n'
    if err:
        instructions += "    Error: Input was not a valid puzzle string\n"
    
    q = questionary.text(
        message="Enter a sudoku puzzle string or ESC to return:\n  ",
        validate=validator,
        style=_puzzle_string_style,
        instruction=instructions,
    )
    q.application.key_bindings = merge_key_bindings(
      [q.application.key_bindings, bindings] #type: ignore
    )
    try:
        result = q.unsafe_ask()
    except KeyboardInterrupt:
        return
    return result

def back_to_menu():
    q = questionary.press_any_key_to_continue(
        "Press any key to return to the main menu"
    )
    q.ask()
    return None