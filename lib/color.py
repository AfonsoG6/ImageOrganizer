import os

class Color:
    """
    A class for defining and applying text colors and styles.
    """
    reset = "\033[0m"
    bold = "\033[01m"
    disable = "\033[02m"
    underline = "\033[04m"
    reverse = "\033[07m"
    strikethrough = "\033[09m"
    invisible = "\033[08m"
    black = "\033[30m"
    red = "\033[31m"
    green = "\033[32m"
    orange = "\033[33m"
    blue = "\033[34m"
    purple = "\033[35m"
    cyan = "\033[36m"
    lightgrey = "\033[37m"
    darkgrey = "\033[90m"
    lightred = "\033[91m"
    lightgreen = "\033[92m"
    yellow = "\033[93m"
    lightblue = "\033[94m"
    pink = "\033[95m"
    lightcyan = "\033[96m"

    @staticmethod
    def color_text(text: str, color: str):
        """
        Colors the given text with the specified color.

        Args:
            text (str): The text to color.
            color (str): The color code to apply.

        Returns:
            str: The colored text.
        """
        do_colors = os.getenv("DO_COLORS", "true").lower() == "true"
        if do_colors:
            return f"{color}{text}{Color.reset}"
        else:
            return text
    
    @staticmethod
    def bold_text(text: str):
        """
        Makes the given text bold.

        Args:
            text (str): The text to make bold.

        Returns:
            str: The bold text.
        """
        return Color.color_text(text, Color.bold)