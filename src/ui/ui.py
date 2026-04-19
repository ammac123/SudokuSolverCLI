import os
import questionary
from rich.panel import Panel
from rich.text import Text
from rich.console import Console

console = Console()

_LOGO = """
███████╗██╗   ██╗██████╗  ██████╗ ██╗  ██╗██╗   ██╗
██╔════╝██║   ██║██╔══██╗██╔═══██╗██║ ██╔╝██║   ██║
███████╗██║   ██║██║  ██║██║   ██║█████╔╝ ██║   ██║
╚════██║██║   ██║██║  ██║██║   ██║██╔═██╗ ██║   ██║
███████║╚██████╔╝██████╔╝╚██████╔╝██║  ██╗╚██████╔╝
╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 
"""

def header():
    logo = Text(_LOGO, style="bold orange")
    console.print(Panel(logo, subtitle="[dim]v0.1.0[/dim]", border_style="orange"))

def main_menu():
    return questionary.select(
        message = "Select",
        choices = [
            questionary.Choice(
            "Input puzzle string (p)", 
                shortcut_key="p", value="p_string"
            ),
            questionary.Choice(
            "Scan image (i)", 
                shortcut_key="i", value="scan_image"
            ),
            questionary.Choice(
            "Settings (s)",
                shortcut_key="s", value="settings"
            ),
            questionary.Separator(),
            questionary.Choice(
            "Quit (q/esc)",
                shortcut_key="q", value="quit"
            ),
        ],
        use_arrow_keys = True,
        use_shortcuts = True
    ).ask()

def main():
    while True:
        console.clear()
        header()

        choice = main_menu()

        if choice == "p_string":
                pass
        elif choice == "scan_image":
                pass
        elif choice == "settings":
                pass
        elif choice == "quit":
                console.print("[dim]Bye👋[/dim]")
                break



if __name__=="__menu__":
    main()