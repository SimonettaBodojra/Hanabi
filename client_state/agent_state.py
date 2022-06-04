import logging

import GameData
from game import Player
from client_state.card_info import Color, Value, DECK_SIZE, DECK_COLOR_STRUCTURE, DECK_VALUE_STRUCTURE, \
    DECK_SINGLE_FIREWORK_STRUCTURE
from client_state.player_hand import Hand, ObservableCard, HiddenCard
from typing import Dict, List, Set
from actions.actions import HintResult, PlayCardResult, DiscardCardResult, Action


class AgentState:

    def __init__(self, game_state: GameData.ServerGameStateData, agent_name: str = "Agent1"):

        self.agent_name: str = agent_name

        # se si è in 3 o meno giocatori si danno 5 carte altrimenti 4
        self.hand_card_number: int = 5 if len(game_state.players) <= 3 else 4
        self.hand: List[HiddenCard] = [HiddenCard() for _ in range(self.hand_card_number)]
        self.players_list: List[Player] = game_state.players
        self.fireworks: Dict[Color, int] = {}
        self.used_blue_token: int = game_state.usedNoteTokens
        self.used_red_token: int = game_state.usedStormTokens
        self.current_player: str = game_state.currentPlayer
        self.discard_pile: Dict[ObservableCard, int] = {}
        self.player_hands: Dict[int, Hand] = {}
        self.my_turn: int = -1
        self.score: int = 0

        # Prendo la lista dei players e per ognuno di essi diverso da me stesso creo o aggiorno la loro mano
        # altrimenti setto solo quando è il mio turno
        for turn, player in enumerate(game_state.players):
            if player.name == self.agent_name:
                self.my_turn = turn
            else:
                self.player_hands[turn] = Hand(player)

        self.is_state_updated = False
        # indexes of the just hinted cards in my hand
        self.just_hinted: Set[int] = set()

        self.update_state(game_state)

    def handle_action_result(self, action: Action):
        action_type = type(action)
        if action_type is HintResult:

            hint_result: HintResult = action
            # se l'hint è stato dato a me allora faccio l'update delle mie carte e del mio stato
            if hint_result.destination_player == self.agent_name:
                self.on_hint_received(hint_result.hint, hint_result.positions)
            # altrimenti metto un flag sulle carte del giocatore corretto
            else:
                for player_hand in self.player_hands.values():
                    if player_hand.player_name == hint_result.destination_player:
                        player_hand.hint_cards(hint_result.hint, hint_result.positions)
                        break

        elif action_type is PlayCardResult or action_type is DiscardCardResult:

            if action.source_player == self.agent_name:
                self.on_new_card(action.card_index, action.card_drawn)
            else:
                for player_hand in self.player_hands.values():
                    if player_hand.player_name == action.source_player:
                        player_hand.draw_card(action.card_index, action.card_drawn)
                        break

        else:
            logging.error("handle_action_result(): Unknown action result")

    def on_hint_received(self, hint: Color or Value, card_indexes: List[int]):
        # Gli hint possono arrivare più volte da vari giocatori se si gioca in più di 2
        # quindi vanno "appesi"
        self.just_hinted = self.just_hinted.union(card_indexes)
        all_card_indexes = set(range(len(self.hand)))
        unhinted_card_indexes = all_card_indexes.difference(card_indexes)
        for i in card_indexes:
            self.hand[i].set_hint(hint)

        for i in unhinted_card_indexes:
            self.hand[i].exclude(hint)

    def on_new_card(self, used_card_index: int, card_drawn: HiddenCard):
        del self.hand[used_card_index]
        if card_drawn is not None:
            assert type(card_drawn) is HiddenCard
            self.hand.append(card_drawn)


    def get_observable_cards(self) -> Dict[ObservableCard, int]:
        # {Colore,valore: count}
        observable_cards = dict()
        for player_hand in self.player_hands.values():
            for card in player_hand.hand:
                previous_card_count = observable_cards.get(card, 0)
                observable_cards[card] = previous_card_count + 1

        for color, card_value in self.fireworks.items():
            for i in range(card_value):
                card = ObservableCard(value=i + 1, color=str(color))
                previous_card_count = observable_cards.get(card, 0)
                observable_cards[card] = previous_card_count + 1

        for card, count in self.discard_pile.items():
            previous_card_count = observable_cards.get(card, 0)
            observable_cards[card] = previous_card_count + count

        for card, count in observable_cards.items():
            assert count <= DECK_SINGLE_FIREWORK_STRUCTURE[card.value]

        return observable_cards

    def get_cards_of_color_value(self) -> (Dict[Color, int], Dict[Value, int]):

        played_for_color: Dict[Color, int] = {color: 0 for color in Color.getColors()}
        played_for_value: Dict[Value, int] = {value: 0 for value in Value.getValues()}

        for observable_card, count in self.get_observable_cards().items():
            played_for_color[observable_card.color] += count
            played_for_value[observable_card.value] += count

        return played_for_color, played_for_value

    def get_count_hinted_cards(self) -> (Dict[Color, int], Dict[Value, int]):

        hinted_color_count = {color: 0 for color in Color.getColors()}
        hinted_value_count = {value: 0 for value in Value.getValues()}

        for hidden_card in self.hand:
            if hidden_card.hint_color is not None:
                hinted_color_count[hidden_card.hint_color] += 1
            if hidden_card.hint_value is not None:
                hinted_value_count[hidden_card.hint_value] += 1

        return hinted_color_count, hinted_value_count

    def update_state(self, game_state: GameData.ServerGameStateData):
        self.used_blue_token = game_state.usedNoteTokens
        self.used_red_token = game_state.usedStormTokens
        self.current_player = game_state.currentPlayer

        # Inizializzo i fireworks come un dizionario che ha per chiave il colore del firework e l'ultimo valore dello stack.
        # 0 quando è vuoto, altrimenti con l'ultima valore della carta nello stack
        self.fireworks: Dict[Color, int] = {}
        self.score = 0
        for color, card_list in game_state.tableCards.items():
            color = Color(color)
            fire_work_len = len(card_list)
            self.fireworks[color] = fire_work_len
            self.score += fire_work_len

        # Inizializzo la pila degli scarti come un dizionario che ha per chiave
        # ObservableCard e valore la quantità scartata
        self.discard_pile: Dict[ObservableCard, int] = {}
        for discarded_card in game_state.discardPile:
            card = ObservableCard(value=discarded_card.value, color=discarded_card.color)
            previous_card_count = self.discard_pile.get(card, 0)
            self.discard_pile[card] = previous_card_count + 1

        # Controllo che la mano dei giocatori sia stata aggiornata in maniera consistente
        for turn, player in enumerate(game_state.players):
            if player.name != self.agent_name:
                self.player_hands[turn].check_hand_consistency(player)

        # observable_card_number = sum(self.get_observable_cards().values())

        # if observable_card_number + self.hand_card_number > DECK_SIZE:
        #     del self.hand[-1]

        self.is_state_updated = True

    @staticmethod
    def __update_card_current_belief2(card: HiddenCard,
                                      remaining_hidden_cards,
                                      all_observable_cards,
                                      played_color_cards,
                                      played_value_cards,
                                      hinted_color_count,
                                      hinted_value_count):

        # se è stato hintato il colore setto le probabilità di quel colore a 1 e il resto a 0
        if card.hasColorHint():
            card.possible_colors = {color: 0 for color in Color.getColors()}
            card.possible_colors[card.hint_color] = 1
        # se è stato hintato il value setto le probabilità di quel value a 1 e il resto a 0
        if card.hasValueHint():
            card.possible_values = {value: 0 for value in Value.getValues()}
            card.possible_values[card.hint_value] = 1

        # se ho entrambi gli hint non faccio più nulla
        if card.hasColorHint() and card.hasValueHint():
            return

        not_excluded_values = Value.getValues().difference(card.excluded_values)
        not_excluded_colors = Color.getColors().difference(card.excluded_colors)

        # se ho solo l'hint sul colore calcolo le probabilità dei value considerando solo le carte di quel colore
        if card.hasColorHint() and not card.hasValueHint():

            excluded_card_number = sum(
                [DECK_SINGLE_FIREWORK_STRUCTURE[excluded_value] for excluded_value in card.excluded_values])
            observable_card_not_excluded = {not_excluded_value: all_observable_cards.get(
                ObservableCard(not_excluded_value.value, card.hint_color.value), 0)
                for not_excluded_value in not_excluded_values}

            observable_card_not_excluded_number = sum(observable_card_not_excluded.values())

            for value in card.possible_values:
                if value in card.excluded_values:
                    card.possible_values[value] = 0
                else:
                    possible_cards = DECK_SINGLE_FIREWORK_STRUCTURE[value] - observable_card_not_excluded[value]
                    total_cards = DECK_COLOR_STRUCTURE[
                                      card.hint_color] - excluded_card_number - observable_card_not_excluded_number

                    assert total_cards != 0

                    card.possible_values[value] = possible_cards / total_cards

        # se ho solo l'hint sul value calcolo le probabilità dei colors considerando solo le carte di quel value
        elif card.hasValueHint() and not card.hasColorHint():

            excluded_card_number = DECK_SINGLE_FIREWORK_STRUCTURE[card.hint_value] * len(card.excluded_colors)
            single_value_possible_color = {
                color: all_observable_cards.get(ObservableCard(card.hint_value.value, color), 0) for color in
                not_excluded_colors}
            observable_card_not_excluded_number = sum(single_value_possible_color.values())

            for color in card.possible_colors:
                # Se il colore rientra nei colori esclusi metto la probabilità a 0
                if color in card.excluded_colors:
                    card.possible_colors[color] = 0
                else:
                    possible_cards = DECK_SINGLE_FIREWORK_STRUCTURE[card.hint_value] - single_value_possible_color[
                        color]
                    total_cards = DECK_VALUE_STRUCTURE[
                                      card.hint_value] - excluded_card_number - observable_card_not_excluded_number

                    assert total_cards != 0

                    card.possible_colors[color] = possible_cards / total_cards

        # non ho nessun hint, calcolo le probabilità considerando solo i not excluded values e colors
        else:
            excluded_cards = 0

            # per ogni colore escluso setto le probabilità a 0 e sommo 10 alle carte escluse per ogni colore
            for excluded_color in card.excluded_colors:
                card.possible_colors[excluded_color] = 0
                excluded_cards += DECK_COLOR_STRUCTURE[excluded_color]

            # per ogni value escluso setto la probabilità a 0 e sommo il numero di carte totali di quel valore (15 in
            # caso di value 1) evitando di contare quelle già incluse per i colori esclusi (in caso di value 1 tolgo
            # 3 carte per ogni colore escluso)
            count_excluded = 0
            for excluded_value in card.excluded_values:
                count_excluded += DECK_SINGLE_FIREWORK_STRUCTURE[excluded_value]
                card.possible_values[excluded_value] = 0
                excluded_cards += DECK_VALUE_STRUCTURE[excluded_value] - (
                            DECK_SINGLE_FIREWORK_STRUCTURE[excluded_value] * len(card.excluded_colors))

            # calcolo tutte le carte giocate not excluded
            not_excluded_observable_cards = 0

            not_excluded_values_dict: Dict[Value: int] = {value: 0 for value in Value.getValues()}
            not_excluded_colors_dict: Dict[Color: int] = {color: 0 for color in Color.getColors()}

            for obs_card, count in all_observable_cards.items():
                if obs_card.color in not_excluded_colors and obs_card.value in not_excluded_values:
                    not_excluded_observable_cards += count
                    not_excluded_values_dict[obs_card.value] += count
                    not_excluded_colors_dict[obs_card.color] += count

            total_cards = DECK_SIZE - excluded_cards - not_excluded_observable_cards
            assert total_cards != 0

            for color in not_excluded_colors:
                possible_cards = DECK_COLOR_STRUCTURE[color] - count_excluded - not_excluded_colors_dict[color]
                card.possible_colors[color] = possible_cards / total_cards

            for value in not_excluded_values:
                possible_cards = DECK_VALUE_STRUCTURE[value] - (DECK_SINGLE_FIREWORK_STRUCTURE[value]*len(card.excluded_colors)) - not_excluded_values_dict[value]
                card.possible_values[value] = possible_cards / total_cards

        assert abs(sum(card.possible_values.values()) - 1) < 0.001
        assert abs(sum(card.possible_colors.values()) - 1) < 0.001

    def update_current_belief(self):

        if not self.is_state_updated:
            raise Exception(f"You have to call the updateState() method first")

        all_observable_cards = self.get_observable_cards()
        played_color_cards, played_value_cards = self.get_cards_of_color_value()
        hinted_color_count, hinted_value_count = self.get_count_hinted_cards()

        played_cards_count = sum([count for count in played_color_cards.values()])
        remaining_hidden_cards = DECK_SIZE - played_cards_count

        for card in self.hand:
            AgentState.__update_card_current_belief2(card, remaining_hidden_cards, all_observable_cards,
                                                     played_color_cards,
                                                     played_value_cards, hinted_color_count, hinted_value_count)

    def get_playable_cards(self) -> Dict[Color, Value]:
        return {color: Value(value + 1) for color, value in self.fireworks.items() if value != Value.FIVE.value}

    def is_card_playable(self, card) -> bool:

        if type(card) is HiddenCard:

            # Una carta è playable in due casi:
            # Ha un valore che può essere messo su qualsiasi firework
            firework_values = list(self.fireworks.values())
            if len(set(firework_values)) == 1 and card.hasValueHint():
                return (card.hint_value.value - 1) == firework_values[0]

            elif not card.hasColorHint() or not card.hasValueHint():
                return False

            card_color = card.hint_color
            card_value = card.hint_value

        elif type(card) is ObservableCard:

            card_color = card.color
            card_value = card.value

        else:
            raise Exception("Unknown card type")

        result = self.get_playable_cards().get(card_color)

        if result is None:
            return False

        return card_value == result

    def is_card_useless(self, card) -> bool:

        if type(card) is HiddenCard:

            # troviamo la carta minima giocabile: tutte le carte sotto quel valore sono useless
            min_firework_value = min(self.fireworks.values())
            if card.hasValueHint() and card.hint_value.value <= min_firework_value:
                return True

            if card.hasColorHint():
                current_firework_value = self.fireworks[card.hint_color]
                if current_firework_value == 5:
                    return True
                discarded_count = self.discard_pile.get(ObservableCard(current_firework_value+1, card.hint_color.value), 0)
                if discarded_count == DECK_SINGLE_FIREWORK_STRUCTURE[Value(current_firework_value+1)]:
                    return True

            if card.hasColorHint() and card.hasValueHint():
                card_color = card.hint_color
                card_value = card.hint_value.value  # ritorna il valore associato all' enum Value
            else:
                return False

        elif type(card) is ObservableCard:
            card_color = card.color
            card_value = card.value.value  # ritorna il valore associato all' enum Value

        else:
            raise Exception("Unknown card type")

        return card_value <= self.fireworks[card_color]  # ritorna il valore associato all' enum Value

    def get_usefulness_probability(self, card: HiddenCard or ObservableCard) -> float:

        playable_cards = self.get_playable_cards()

        if type(card) is HiddenCard:
            # HiddenCard è useful se ha una probabilità alta di essere una determinata combinazione colore/valore
            probability_list = []
            for color, value in playable_cards.items():
                probability_list.append(card.possible_colors[color] * card.possible_values[value])

            max_probability = max(probability_list)

        elif type(card) is ObservableCard:
            # ObsevableCard è useful se è quella subito dopo la playable

            if (card.value.value + 1) == playable_cards[card.color].value:
                max_probability = 1
            else:
                max_probability = 0

        else:
            raise Exception("Unknown card type")

        return max_probability

    def get_dispensable_probability(self, card: HiddenCard or ObservableCard) -> float:
        critical_cards = self.get_critical_cards()

        if type(card) is HiddenCard:

            #HiddenCard sacrificabile se ha una bassa probabilità di essere critica
            probability_list = []
            for critical_card in critical_cards:
                probability_list.append(card.possible_colors[critical_card.color] * card.possible_values[critical_card.value])

            max_probability = max(probability_list)

        elif type(card) is ObservableCard:

            #ObservableCard sacrificabile se non è critica
            if card in critical_cards:
                max_probability = 0
            else:
                max_probability = 1

        else:
            raise Exception("Unknown card type")

        return 1-max_probability

    def check_card_usability(self, card: HiddenCard, check: str, useful_threshold: float = .7,
                             dispensable_threshold: float = .2) -> bool:

        if check == "playable":
            return self.is_card_playable(card)
        elif check == "useful":
            return useful_threshold <= self.get_usefulness_probability(card)
        elif check == "dispensable":
            return dispensable_threshold <= self.get_dispensable_probability(card)
        elif check == "useless":
            return self.is_card_useless(card)
        else:
            raise Exception("Wrong usability check!")

    def get_critical_cards(self) -> Set[ObservableCard]:
        firework_structure = DECK_SINGLE_FIREWORK_STRUCTURE
        critical_cards = set()

        for color, count in self.fireworks.items():
            # partendo da count+1 sto già filtrando le carte non critiche per definizione
            for value in range(count + 1, Value.FIVE.value + 1):
                value = Value(value)
                card = ObservableCard(value, color)
                discarded_count = self.discard_pile.get(card, 0)
                if firework_structure[value] - 1 == discarded_count:
                    critical_cards.add(card)

        return critical_cards

    def __str__(self) -> str:
        fireworks = ""
        for idx, (color, count) in enumerate(self.fireworks.items()):
            fireworks += f"{color}: {count}"
            if idx < len(self.fireworks) - 1:
                fireworks += ", "

        discard_pile = ""
        for idx, (card, count) in enumerate(self.discard_pile.items()):
            discard_pile += f"({card.value} {card.color}): {count}"
            if idx < len(self.discard_pile) - 1:
                discard_pile += ", "

        players = ""
        for idx in self.player_hands:
            players += f"{self.player_hands[idx]}\n"

        my_cards = ""
        for idx, card in enumerate(self.hand):
            my_cards += f"\tcard {idx} -> value: {card.possible_values} - color: {card.possible_colors}\n"

        return f"""
        FIREWORKS: {{{fireworks}}}
        DISCARD_PILE: {{{discard_pile}}}
        TOKENS: Blue({self.used_blue_token}/8) - Red({self.used_red_token}/3)
        SCORE: {self.score}/25

        PLAYERS:
        {players}

        CURRENT BELIEF:
        {my_cards} 
        """
