import sys

from recommendation.utils.chat_runner import menu_loop


def configure_console() -> None:
    """Keep Persian CLI output usable in Windows terminals with legacy code pages."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if __name__ == "__main__":
    configure_console()
    menu_loop()
