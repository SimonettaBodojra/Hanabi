import logging
from typing import Dict, List, Set

from client_state.card_info import Value, Color, DECK_VALUE_STRUCTURE
from game import Player


class Hand:

    def __init__(self, player: Player):
        self.player_name = player.name
        self.hand = [ObservableCard(c.value, c.color) for c in player.hand]

    def __str__(self):
        return f"{self.player_name} - {self.hand}"

    def __repr__(self):
        return self.__str__()

    def check_hand_consistency(self, player: Player):
        for idx, card in enumerate(player.hand):
            old_card = self.hand[idx]
            assert old_card.color.value == card.color and old_card.value.value == card.value
            # if not (old_card.color.value == card.color and old_card.value.value == card.value):
            #     print("hand inconsistency")

    def hint_cards(self, hint: Value or Color, positions: List[int]):
        for pos in positions:
            self.hand[pos].set_hint(hint)

    def draw_card(self, used_card_index: int, drawn_card):
        del self.hand[used_card_index]
        if drawn_card is not None:
            assert type(drawn_card) is ObservableCard
            self.hand.append(drawn_card)


class ObservableCard:

    def __init__(self, value: int, color: str, is_color_hinted: bool = False, is_value_hinted: bool = False):
        self.value = Value(value)
        self.color = Color(color)
        self.is_color_hinted = is_color_hinted
        self.is_value_hinted = is_value_hinted

    def __str__(self):
        return f"({self.color} {self.value})"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return (self.color, self.value).__hash__()

    def __eq__(self, other):
        if not hasattr(other, 'color') or not hasattr(other, 'value'):
            return False

        return self.color == other.color and self.value == other.value

    def is_hintable(self):
        return not (self.is_color_hinted and self.is_value_hinted)

    def set_hint(self, hint: Color or Value):
        if type(hint) is Color:
            self.is_color_hinted = True
        elif type(hint) is Value:
            self.is_value_hinted = True
        else:
            raise Exception("Unknown hint type")


class HiddenCard:

    def __init__(self, is_new: bool = False):

        self.possible_values: Dict[Value: float] = {value: DECK_VALUE_STRUCTURE[value] / 50 for value in Value.getValues()}
        self.possible_colors: Dict[Color: float] = {color: 1 / len(Color.getColors()) for color in Color.getColors()}
        self.hint_color = None
        self.hint_value = None
        self.excluded_values: Set[Value] = set()
        self.excluded_colors: Set[Color] = set()
        self.is_new = is_new

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

    def set_hint(self, hint: Color or Value):
        if type(hint) is Color:
            self.set_hint_color(hint)
        elif type(hint) is Value:
            self.set_hint_value(hint)
        else:
            raise Exception("Unknown hint type")

    def exclude(self, hint: Color or Value):
        hint_type = type(hint)

        # se è già stata hintata non c'è bisogno di aggiungere un valore ai colori esclusi
        if hint_type is Color and self.hint_color is None:
            self.excluded_colors.add(hint)

        # se è già stata hintata non c'è bisogno di aggiungere un valore ai valori esclusi
        elif hint_type is Value:
            self.excluded_values.add(hint)

    def hasValueHint(self) -> bool:
        return self.hint_value is not None

    def hasColorHint(self) -> bool:
        return self.hint_color is not None

if __name__ == '__main__':
    c1 = ObservableCard(2, "red")
    c2 = ObservableCard(2, "red")
    d = dict()
    d[c1] = 1
    d[c2] = 2
    print(d)
