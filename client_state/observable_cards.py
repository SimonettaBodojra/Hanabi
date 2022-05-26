from card_info import Color, Value, DECK_STRUCTURE
from copy import deepcopy


class ObservableCards:

    def __init__(self):
        self.fireworks = {color: None for color in Color.getColors()}
        self.discard_pile = {}

        for color in Color.getColors():
            for value in Value.getValues():
                self.discard_pile[(color, value)] = 0

        self.players_cards = deepcopy(self.discard_pile)

    def updateFirework(self, color: Color, value: Value):
        self.fireworks[color] = value

    def discardCard(self, color: Color, value: Value):
        discarded_count = self.discard_pile[(color, value)]

        if value == Value.FIVE and discarded_count >= 1:
            raise Exception(f"DISCARD_PILE: You cannot discard more than one {color.toString()} 5")
        elif value == Value.ONE and discarded_count >= 3:
            raise Exception(f"DISCARD_PILE: You cannot discard more than three {color.toString()} 1s")
        elif discarded_count >= 2:
            raise Exception(f"DISCARD_PILE: You cannot discard more than two {color.toString()} {value.toString()}s")

        self.discard_pile[(color, value)] = discarded_count + 1

    def removePlayersCard(self, color: Color, value: Value):
        card_count = self.players_cards[(color, value)]

        if card_count <= 0:
            raise Exception("PLAYER_CARDS: You cannot remove a card the player doesn't own")

        self.players_cards[(color, value)] = card_count - 1

    def addPlayersCard(self, color: Color, value: Value):
        card_count = self.players_cards[(color, value)]

        if value == Value.FIVE and card_count >= 1:
            raise Exception(f"PLAYER_CARDS: You cannot add more than one {color} 5 to player cards")
        elif value == Value.ONE and card_count >= 3:
            raise Exception(f"PLAYER_CARDS: You cannot add more than three {color} 1s to player cards")
        elif card_count >= 2:
            raise Exception(f"PLAYER_CARDS: You cannot add more than two {color} {value}s to player cards")

        self.players_cards[(color, value)] = card_count + 1

    def remainingCard(self, color: Color, value: Value) -> int:
        discarded_count = self.discard_pile[(color, value)]
        player_cards_count = self.players_cards[(color, value)]

        total_count = discarded_count + player_cards_count

        firework: Color = self.fireworks[color]

        if firework is not None and firework.value >= value.value:
            total_count += 1

        remaining_cards = None
        exception = None
        if value == Value.FIVE:
            remaining_cards = 1 - total_count
            exception = Exception(f"REMAINING_CARDS: Found more than one {color} 5")
        elif value == Value.ONE:
            remaining_cards = 3 - total_count
            exception = Exception(f"REMAINING_CARDS: Found more than three {color} 1s")
        elif total_count >= 2:
            remaining_cards = 2 - total_count
            exception = Exception(f"REMAINING_CARDS: Found more than two {color} {value}s")

        if remaining_cards < 0:
            raise exception

        return remaining_cards


if __name__ == '__main__':
    playedCards = ObservableCards()
    playedCards.addPlayersCard(Color.RED, value=Value.ONE)
    playedCards.addPlayersCard(Color.RED, value=Value.ONE)

    print(playedCards.remainingCard(Color.RED, value=Value.ONE))
