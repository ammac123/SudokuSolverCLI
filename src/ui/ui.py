import os
import questionary
from time import sleep
from rich.panel import Panel
from rich.text import Text
from src.ui.navigation import loading, main_menu, console


def main():
    console.clear()
    loading()
    main_menu()



if __name__=="__main__":
    main()