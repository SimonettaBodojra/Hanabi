from enum import Enum
from typing import Set


class Value(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

    def __str__(self) -> str:
        if self == Value.ONE:
            return "1"
        elif self == Value.TWO:
            return "2"
        elif self == Value.THREE:
            return "3"
        elif self == Value.FOUR:
            return "4"
        else:
            return "5"

    @staticmethod
    def getValues() -> Set:
        return {Value.ONE, Value.TWO, Value.THREE, Value.FOUR, Value.FIVE}


class Color(Enum):
    WHITE = 0
    RED = 1
    BLUE = 2
    YELLOW = 3
    GREEN = 4

    def __str__(self) -> str:
        if self == Color.WHITE:
            return "White"
        elif self == Color.RED:
            return "Red"
        elif self == Color.BLUE:
            return "Blue"
        elif self == Color.YELLOW:
            return "Yellow"
        else:
            return "Green"

    @staticmethod
    def getColors() -> Set:
        return {Color.WHITE, Color.RED, Color.BLUE, Color.YELLOW, Color.GREEN}

    @staticmethod
    def fromStringColor(color: str):
        if color == "white":
            return Color.WHITE
        elif color == "red":
            return Color.RED
        elif color == "green":
            return Color.GREEN
        elif color == "blue":
            return Color.BLUE
        elif color == "yellow":
            return Color.YELLOW
        else:
            raise Exception("Unknown card color")


DECK_VALUE_STRUCTURE = {Value.ONE: 15, Value.TWO: 10, Value.THREE: 10, Value.FOUR: 10, Value.FIVE: 5}
DECK_COLOR_STRUCTURE = {Color.WHITE: 10, Color.YELLOW: 10, Color.GREEN: 10, Color.BLUE: 10, Color.RED: 10}

DECK_SIZE = 50