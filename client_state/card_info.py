from enum import Enum
from typing import Set


class Value(Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5

    def __str__(self) -> str:
        return str(self.value)

    @staticmethod
    def getValues() -> Set:
        return {Value.ONE, Value.TWO, Value.THREE, Value.FOUR, Value.FIVE}


class Color(Enum):
    WHITE = "white"
    RED = "red"
    BLUE = "blue"
    YELLOW = "yellow"
    GREEN = "green"

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def getColors() -> Set:
        return {Color.WHITE, Color.RED, Color.BLUE, Color.YELLOW, Color.GREEN}


DECK_VALUE_STRUCTURE = {Value.ONE: 15, Value.TWO: 10, Value.THREE: 10, Value.FOUR: 10, Value.FIVE: 5}
DECK_COLOR_STRUCTURE = {Color.WHITE: 10, Color.YELLOW: 10, Color.GREEN: 10, Color.BLUE: 10, Color.RED: 10}

DECK_SIZE = 50