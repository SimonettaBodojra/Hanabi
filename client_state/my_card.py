from typing import Set

from card_info import Value, Color


class MyCard:

    def __init__(self, possible_values: Set[Value] = None, possible_colors: Set[Color] = None):

        self.possible_values = possible_values if possible_values is not None else Value.getValues()
        self.possible_colors = possible_colors if possible_colors is not None else Color.getColors()

    def single_choice_probability(self, value: Value = None, color: Color = None) -> float:
        if value is None and color is None:
            raise Exception("A value or a color must be provided")

        value_probability = None
        color_probability = None

        if value is not None:
            value_probability = 0 if value not in self.possible_values else 1 / len(self.possible_values)

        if color is not None:
            color_probability = 0 if color not in self.possible_colors else 1 / len(self.possible_colors)

        if value_probability is not None:
            if color_probability is not None:
                return value_probability * color_probability
            else:
                return value_probability
        else:
            return color_probability

    def colors_probability(self, colors: Set[Color]) -> float:
        if colors is None:
            raise Exception("Set of colors cannot be None")

        probability = 0
        for color in colors:
            if color in self.possible_colors:
                probability += 1 / len(self.possible_colors)

        return probability

    def values_probability(self, values: Set[Value]) -> float:
        if values is None:
            raise Exception("Set of colors cannot be None")

        probability = 0
        for value in values:
            if value in self.possible_values:
                probability += 1 / len(self.possible_values)

        return probability

# if __name__ == '__main__':
#     card = Card(possible_values={Values.ONE, Values.THREE, Values.FIVE}, possible_colors={Colors.RED, Colors.BLUE})
#
#     print(card.probability(value=Values.ONE))
#     print(card.probability(value=Values.TWO))
#     print(card.probability(color=Colors.RED))
#     print(card.probability(color=Colors.WHITE))
#     print(card.probability(value=Values.ONE, color=Colors.RED))
#     print(card.probability(value=Values.TWO, color=Colors.RED))
#     print(card.probability(value=Values.ONE, color=Colors.WHITE))
