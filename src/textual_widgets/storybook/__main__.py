"""Entry point fuer `python -m textual_widgets.storybook`."""
from textual_widgets.storybook.app import StorybookApp


def main() -> None:
    StorybookApp().run()


if __name__ == "__main__":
    main()
