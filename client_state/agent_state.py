import GameData
from game import Player
from card_info import Color, Value, DECK_SIZE, DECK_COLOR_STRUCTURE, DECK_VALUE_STRUCTURE
from player_hand import Hand, ObservableCard, HiddenCard
from typing import Dict, List


class AgentState:

    def __init__(self, game_state: GameData.ServerGameStateData, agent_name: str = "Agent1"):

        self.agent_name: str = agent_name

        # se si è in 3 o meno giocatori si danno 5 carte altrimenti 4
        self.hand_card_number: int = 5 if len(game_state.players) <= 3 else 4
        self.hand: List[HiddenCard] = [HiddenCard() for _ in range(self.hand_card_number)]
        self.players_list: List[Player] = game_state.players
        self.fireworks: Dict[Color: Value] = None
        self.used_blue_token: int = game_state.usedNoteTokens
        self.used_red_token: int = game_state.usedStormTokens
        self.current_player: str = game_state.currentPlayer
        self.discard_pile: Dict[ObservableCard: int] = None
        self.player_hands: Dict[int: Hand] = None
        self.my_turn: int = -1
        for turn, player in enumerate(game_state.players):
            if player.name == self.agent_name:
                self.my_turn = turn
                break
        self.update_state(game_state)
        self.is_state_updated = False

    def get_observable_cards(self) -> Dict[ObservableCard: int]:
        #{Colore,valore: count}
        observable_cards = dict()
        for player_hand in self.player_hands.values():
            for card in player_hand.hand:
                previous_card_count = observable_cards.get(card, 0)
                observable_cards[card] = previous_card_count + 1

        for color, card_value in self.fireworks.items():
            for i in range(card_value.value):
                card = ObservableCard(value=i+1, color=color)
                previous_card_count = observable_cards.get(card, 0)
                observable_cards[card] = previous_card_count + 1

        for (color, value), count in self.discard_pile.items():
            card = ObservableCard(value=value, color=color)
            previous_card_count = observable_cards.get(card, 0)
            observable_cards[card] = previous_card_count + count

        return observable_cards

    def get_cards_of_color(self) -> Dict[Color: int]:

        played_for_color: Dict[Color: int] = {}

        for observable_card, count in self.get_observable_cards().items():
            previous_card_count = played_for_color.get(observable_card.color, 0)
            played_for_color[observable_card.color] = previous_card_count + count

        return played_for_color

    def get_cards_of_value(self) -> Dict[Value: int]:

        played_for_value: Dict[Value: int] = {}

        for observable_card, count in self.get_observable_cards().items():
            previous_card_count = played_for_value.get(observable_card.value, 0)
            played_for_value[observable_card.value] = previous_card_count + count

        return played_for_value

    def update_state(self, game_state: GameData.ServerGameStateData):
        self.used_blue_token = game_state.usedNoteTokens
        self.used_red_token = game_state.usedStormTokens
        self.current_player = game_state.currentPlayer

        # Inizializzo i fireworks come un dizionario che ha per chiave il colore del firework e l'ultimo valore dello stack.
        # 0 quando è vuoto, altrimenti con l'ultima valore della carta nello stack
        self.fireworks: Dict[Color: Value]
        for color, card_list in game_state.tableCards.items():
            color = Color.fromStringColor(color)
            self.fireworks[color] = 0 if len(card_list) == 0 else Value(card_list[-1].value)

        # Inizializzo la pila degli scarti come un dizionario che ha per chiave
        # ObservableCard e valore la quantità scartata
        self.discard_pile: Dict[ObservableCard: int]
        for discarded_card in game_state.discardPile:
            card = ObservableCard(value=discarded_card.value, color=discarded_card.color)
            previous_card_count = self.discard_pile.get(card, 0)
            self.discard_pile[card] = previous_card_count + 1

        for turn, player in enumerate(game_state.players):
            if player.name != self.agent_name:
                self.player_hands[turn] = Hand(player=player)

        self.is_state_updated = True

    def __update_card_current_belief(self, card: HiddenCard, remaining_hidden_cards, played_color_cards, played_value_cards):

        if card.hint_color is None:
            for color in card.possible_colors:
                card.possible_colors[color] = (DECK_COLOR_STRUCTURE[color]-played_color_cards[color]) / remaining_hidden_cards
            assert abs(sum(card.possible_colors.values()) - 1.0) < 0.001

        if card.hint_value is None:
            for value in card.possible_values:
                card.possible_values[value] = (DECK_VALUE_STRUCTURE[value] - played_value_cards[value]) / remaining_hidden_cards
            assert abs(sum(card.possible_values.values()) - 1.0) < 0.001


    def update_current_belief(self):

        if not self.is_state_updated:
            raise Exception(f"You have to call the updateState() method first")

        played_color_cards = self.get_cards_of_color()
        played_value_cards = self.get_cards_of_value()

        played_cards_count = sum([count for count in played_color_cards.values()])
        remaining_hidden_cards = DECK_SIZE - played_cards_count

        for card in self.hand:
            self.__update_card_current_belief(card, remaining_hidden_cards, played_color_cards, played_value_cards)