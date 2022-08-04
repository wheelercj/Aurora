import sys

from ssg.generate_site import generate_site
from ssg.settings import settings  # noqa
from ssg.settings import show_settings_window
from ssg.settings import validate_settings


def main() -> None:
    global settings
    arg = " ".join(sys.argv[1:])
    if not arg:
        generate_site()
    elif arg in ("-h", "--help"):
        print_cli_help()
    elif arg in ("-s", "--settings"):
        settings = show_settings_window(settings)
        if not validate_settings(settings.data):
            settings = show_settings_window(settings)
    else:
        print("Unknown argument:", arg)
        print_cli_help()


def print_cli_help() -> None:
    print("Mac/Linux usage: python3 cli.py [OPTION]")
    print("Windows usage: py cli.py [OPTION]")
    print("Use no option to generate the site.")
    print("Options:")
    print("  -h, --help    Show this help message.")
    print("  -s, --settings    Show the settings window.")


if __name__ == "__main__":
    main()
