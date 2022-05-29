from game import Player
from typing import Dict
from client_state.card_info import Value, Color, DECK_VALUE_STRUCTURE

class Hand:

    def __init__(self, player: Player):
        self.player_name = player.name
        self.hand = [ObservableCard(c.value, c.color) for c in player.hand]

    def __str__(self):
        tmp_str = f"Player: {self.player_name}"
        for i, c in enumerate(self.hand):
            tmp_str += f"\n\t- {i}: {c}"
        return tmp_str


class ObservableCard:

    def __init__(self, value: int, color: str, is_color_hinted: bool = False, is_value_hinted: bool = False):

        self.value = Value(value)
        self.color = Color(color)
        self.is_color_hinted = is_color_hinted
        self.is_value_hinted = is_value_hinted

    def __str__(self):
        return f"{self.color} {self.value}"

    def __hash__(self):
        return (self.color, self.value).__hash__()

    def is_hintable(self):
        return not (self.is_color_hinted and self.is_color_hinted)


class HiddenCard:

    def __init__(self):

        self.possible_values: Dict[Value: float] = {value: DECK_VALUE_STRUCTURE[value] / 50 for value in Value.getValues()}
        self.possible_colors: Dict[Color: float] = {color: 1 / len(Color.getColors()) for color in Color.getColors()}
        self.hint_color = None
        self.hint_value = None

    def set_hint_color(self, hinted_color: Color):

        self.hint_color = hinted_color
        for color in self.possible_colors:
            if hinted_color == color:
                self.possible_colors[color] = 1.0
            else:
                self.possible_colors[color] = 0.0

    def set_hint_value(self, hinted_value: Value):

        self.hint_value = hinted_value
        for value in self.possible_values:
            if hinted_value == value:
                self.possible_values[value] = 1
            else:
                self.possible_values[value] = 0


if __name__ == '__main__':
    from game import Card

    p = Player("ciao")
    p.hand = [Card(0, 1, "yellow") for _ in range(3)]

    c = HiddenCard()
    c.set_hint_color(Color.YELLOW)
    print(c.possible_colors)
