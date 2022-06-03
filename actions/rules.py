from abc import ABC, abstractmethod
from typing import Tuple, List, Dict

from client_state.agent_state import AgentState
from client_state.card_info import Color, Value
from actions.actions import Action, Hint, PlayCard, DiscardCard
import random
import logging

class Rule(ABC):

    def __init__(self, state: AgentState):
        self.state = state
        self.sender = self.state.agent_name

    @abstractmethod
    def rule_to_action(self) -> Action:
        raise NotImplementedError


# ------ PLAY RULES (4) ------

class PlaySafeCard(Rule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        # List of the playable cards indexes
        playable_cards_indexes = [idx for idx, hidden_card in enumerate(self.state.hand)
                                  if self.state.check_card_usability(hidden_card, "playable")]

        if len(playable_cards_indexes) == 0:
            logging.debug("There are no playable cards")
            return None

        return PlayCard(self.sender, playable_cards_indexes[0])


class PlayRandomCard(Rule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_red_token > 1:
            return None

        random_index = random.choice(range(self.state.hand_card_number))

        return PlayCard(self.sender, random_index)


class PlayUsefulCard(Rule):
    def __init__(self, state: AgentState, usefulness_threshold: float):
        super().__init__(state)

        self.usefulness_threshold = usefulness_threshold

    def rule_to_action(self) -> Action:
        if self.state.used_red_token > 1:
            return None

        useful_cards_indexes = [idx for idx, hidden_card in enumerate(self.state.hand)
                                if self.state.check_card_usability(hidden_card, "useful",
                                                                   useful_threshold=self.usefulness_threshold)]

        if len(useful_cards_indexes) == 0:
            logging.debug("There are no useful cards")
            return None

        return PlayCard(self.sender, useful_cards_indexes[0])


class PlayJustHinted(Rule):

    def __init__(self, state: AgentState, usefulness_threshold: float):
        super().__init__(state)

        self.usefulness_threshold = usefulness_threshold

    def rule_to_action(self) -> Action:
        if self.state.used_red_token > 1:
            return None

        max_prob = .0
        useful_card_index = 0
        # prendo tutti gli indici  delle carte appena hintate
        for card_index in self.state.just_hinted:
            curr_card = self.state.hand[card_index]
            # calcolo la probabilitò di quella carta che sia giocabile
            curr_prob = self.state.get_usefulness_probability(curr_card)
            # trovo la carta con maggior probabilità di essere giocate tra quella appena hintate
            if max_prob < curr_prob:
                useful_card_index = card_index
                max_prob = curr_prob

        # se la confidenza sulla giocabilità è troppo bassa allora non usare questa action
        if max_prob < self.usefulness_threshold:
            return None

        return PlayCard(self.sender, useful_card_index)

class PlayUsefulValueCard(Rule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_red_token != 0:
            return None



# ------ DISCARD RULES (6) ------

class DiscardUselessCard(Rule):
    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        # List of the playable cards indexes
        useless_cards_indexes = [idx for idx, hidden_card in enumerate(self.state.hand)
                                 if self.state.check_card_usability(hidden_card, "useless")]

        if len(useless_cards_indexes) == 0:
            logging.debug("There are no useless cards")
            return None

        return DiscardCard(self.sender, useless_cards_indexes[0])


class DiscardRandomCard(Rule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        random_index = random.choice(range(self.state.hand_card_number))
        return DiscardCard(self.sender, random_index)


class DiscardDispensableCard(Rule):
    def __init__(self, state: AgentState, dispensable_threshold: float):
        super().__init__(state)

        self.dispensable_threshold = dispensable_threshold

    def rule_to_action(self) -> Action:
        dispensable_cards_indexes = [idx for idx, hidden_card in enumerate(self.state.hand)
                                     if self.state.check_card_usability(hidden_card, "dispensable",
                                                                        dispensable_threshold=self.dispensable_threshold)]
        if len(dispensable_cards_indexes) == 0:
            logging.debug("There are no dispensable cards")
            return None

        return DiscardCard(self.sender, dispensable_cards_indexes[0])


class DiscardJustHinted(Rule):

    def __init__(self, state: AgentState, dispensable_threshold: float):
        super().__init__(state)

        self.dispensable_threshold = dispensable_threshold

    def rule_to_action(self) -> Action:
        max_prob = .0
        dispensable_card_index = 0
        for card_index in self.state.just_hinted:
            curr_card = self.state.hand[card_index]
            curr_prob = self.state.get_dispensable_probability(curr_card)
            if max_prob < curr_prob:
                dispensable_card_index = card_index
                max_prob = curr_prob

        if max_prob < self.dispensable_threshold:
            return None

        return DiscardCard(self.sender, dispensable_card_index)


class DiscardOldestUnhintedCard(Rule):
    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:

        for count, hidden_card in enumerate(self.state.hand):
            if hidden_card.hint_color is None and hidden_card.hint_color is None:
                break

        return DiscardCard(self.sender, count)


# ------ HINT RULES (6) ------

class HintRule(Rule):

    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state)

        self.next_player = next_player

    def hintable_players(self):

        if self.next_player:
            next_player_turn = (self.state.my_turn + 1) % len(self.state.players_list)
            next_destination_player = self.state.players_list[next_player_turn].name
            next_destination_player_hand = self.state.player_hands[next_player_turn].hand
            return [(next_destination_player, next_destination_player_hand)]

        else:

            n_players = len(self.state.players_list)
            available_blue_tokens = 8 - self.state.used_blue_token

            if available_blue_tokens >= n_players:
                hintable_players = [(self.state.my_turn + i) % len(self.state.players_list) for i in
                                    range(1, n_players)]

            else:
                hintable_players = [(self.state.my_turn + i) % len(self.state.players_list) for i in
                                    range(1, available_blue_tokens + 1)]

            hintable_players_info = [(self.state.players_list[player].name, self.state.players_list[player].hand) for
                                     player in hintable_players]

            return hintable_players_info

    @staticmethod
    def choose_random_hint(destination_player_hand):
        index_list = range(0, len(destination_player_hand))
        rand_card_index = list(filter(lambda x: destination_player_hand[x].is_hintable(), index_list))

        if len(rand_card_index) == 0:
            return None

        rand_index = random.choice(rand_card_index)
        rand_card = destination_player_hand[rand_index]

        if rand_card.is_color_hinted:
            return rand_card.value
        elif rand_card.is_value_hinted:
            return rand_card.color
        else:
            hints = [rand_card.value, rand_card.color]
            return random.choice(hints)

    def get_hint(self, check: str, players: List, useful_threshold: float = .7, dispensable_threshold: float = .7):
        card_indexes = []

        for player in players:
            card_indexes = [idx for idx, card in enumerate(player[1])
                            if self.state.check_card_usability(card, check,
                                                               useful_threshold=useful_threshold,
                                                               dispensable_threshold=dispensable_threshold)]
            if len(card_indexes) > 0:
                break

        if len(card_indexes) == 0:
            return None, None

        rand_index = random.choice(card_indexes)
        random_card = player[1][rand_index]

        if random_card.is_color_hinted:
            return player, random_card.value
        elif random_card.is_value_hinted:
            return player, random_card.color
        else:
            hints = [random_card.value, random_card.color]
            return player, random.choice(hints)

    # @staticmethod
    # def set_hint_flag(hint: Value or Color, player: Tuple):
    #
    #     if type(hint) is Color:
    #         for card_index in range(len(player[1])):
    #             card = player[1][card_index]
    #             if card.color == hint:
    #                 player[1][card_index].is_color_hinted = True
    #
    #     elif type(hint) is Value:
    #         for card_index in range(len(player[1])):
    #             card = player[1][card_index]
    #             if card.value == hint:
    #                 player[1][card_index].is_value_hinted = True
    #
    #     else:
    #         raise Exception("Unknown hint type")


class HintRandom(HintRule):

    def __init__(self, state: AgentState, next_player: bool):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:

        if self.state.used_blue_token == 8:
            return None

        random_player_tuple = random.choice(self.hintable_players())

        hint, hinted_index = HintRule.choose_random_hint(random_player_tuple[1])

        if hint is None:
            return None

        # self.set_hint_flag(hint, random_player_tuple)

        return Hint(self.sender, random_player_tuple[0], hint)


class HintPlayableCard(HintRule):

    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:

        if self.state.used_blue_token == 8:
            return None

        player, hint = self.get_hint(check="playable", players=self.hintable_players())

        if hint is None:
            return None

        # self.set_hint_flag(hint, player)

        return Hint(self.sender, player[0], hint)


class HintUsefulCard(HintRule):
    def __init__(self, state: AgentState, next_player: bool = True, usefulness_threshold: float = .7):
        super().__init__(state, next_player)

        self.usefulness_threshold = usefulness_threshold

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        player, hint = self.get_hint(check="useful", players=self.hintable_players(),
                                     useful_threshold=self.usefulness_threshold)

        if hint is None:
            return None

        # self.set_hint_flag(hint, player)

        return Hint(self.sender, player[0], hint)


class HintFullKnowledge(HintRule):
    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        players = self.hintable_players()
        hintable_card_indexes = []
        selected_player = None
        for player in players:
            hintable_card_indexes = [idx for idx, card in enumerate(player[1])
                                     if (card.is_value_hinted and not card.is_color_hinted) or
                                     (card.is_color_hinted and not card.is_value_hinted)]

            if len(hintable_card_indexes) > 0:
                selected_player = player
                break

        if selected_player is None:
            return None

        rand_hint = random.choice(hintable_card_indexes)
        rand_card = selected_player[1][rand_hint]

        if rand_card.is_color_hinted:
            hint = rand_card.value
        else:
            hint = rand_card.color

        # self.set_hint_flag(hint, selected_player)

        return Hint(self.sender, selected_player[0], hint)


class HintMostInformation(HintRule):

    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        players = self.hintable_players()
        # qui sarà presente la lista dei player con i rispettivi massimi di carte di un colore e di un valore
        player_card_info: Dict[str, ((Color, int), (Value, int))] = {}

        # ciclo sui player e calcolo per colore e valore la loro rispettiva quantità escludendo le carte già hintate
        for player in players:
            player_hand = player[1]
            color_dict: Dict[Color, int] = {color: 0 for color in Color.getColors()}
            value_dict: Dict[Value, int] = {value: 0 for value in Value.getValues()}

            for card in player_hand:
                if not card.is_color_hinted:
                    color_dict[card.color] += 1
                if not card.is_value_hinted:
                    value_dict[card.value] += 1

            # calcolo il massimo numero di carte di un colore e valore per quel player e li inserisco nella struttura sopra
            max_color = max(color_dict.items(), key=lambda x: x[1])
            max_value = max(value_dict.items(), key=lambda x: x[1])
            player_card_info[player[0]] = (max_color, max_value)

        # tra tutti i player scelgo il player che può essere hintato che ha il maggior numero di carte hintabili
        max_color_player = max(player_card_info.items(), key=lambda x: x[1][0][1])
        max_value_player = max(player_card_info.items(), key=lambda x: x[1][1][1])

        max_color_player = (max_color_player[0], max_color_player[1][0])
        max_value_player = (max_value_player[0], max_value_player[1][1])

        # una volta scelto il player controllo se ottengo più hint con il colore o con il valore altrimenti scelgo a caso
        if max_value_player[1][1] > max_color_player[1][1]:
            max_player = max_value_player
        elif max_value_player[1][1] < max_color_player[1][1]:
            max_player = max_color_player
        else:
            max_player = random.choice([max_color_player, max_value_player])

        # player_hand = None
        # for player in players:
        #     if player[0] == max_player[0]:
        #         player_hand = player[1]
        #         break

        # self.set_hint_flag(max_player[1][0], player_hand)

        return Hint(self.sender, max_player[0], max_player[1][0])


class HintCritical(HintRule):

    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        players = self.hintable_players()
        critical_cards = self.state.get_critical_cards()
        selected_player = None
        selected_card = None
        for player in players:
            player_cards = set(player[1])
            intersection = critical_cards.intersection(player_cards)
            if len(intersection) == 0:
                selected_player = player
                selected_card = random.choice(list(intersection))
                break

        if selected_player is None:
            return None

        if selected_card.is_color_hinted:
            hint = selected_card.value
        elif selected_card.is_value_hinted:
            hint = selected_card.color
        else:
            hints = [selected_card.value, selected_card.color]
            hint = random.choice(hints)

        # self.set_hint_flag(hint, selected_player)

        return Hint(self.sender, selected_player[0], hint)


class HintOnes(HintRule):
    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:

        if self.state.used_blue_token == 8:
            return None

        empty_stacks = [stack[1] for stack in self.state.fireworks.items() if stack[1] == 0]

        if len(empty_stacks) == 0:
            return None

        players = self.hintable_players()
        selected_player = None

        for player in players:
            ones_count = len([card.value for card in player[1]
                              if card.value == Value.ONE and not card.is_value_hinted])

            if ones_count > 0:
                selected_player = player

        if selected_player is None:
            return None

        # self.set_hint_flag(Value.ONE, selected_player)

        return Hint(self.sender, selected_player[0], Value.ONE)

class HintUnknown(HintRule):
    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        players = self.hintable_players()
        selected_player = None

        for player in players:
            unhinted_card_idxs = [card for card in player[1] if not card.is_color_hinted and not card.is_value_hinted]
            if len(unhinted_card_idxs) > 0:
                selected_player = player

        if selected_player is None:
            return None

        rand_index = random.choice(unhinted_card_idxs)
        random_card = selected_player[1][rand_index]

        hints = [random_card.value, random_card.color]
        hint = random.choice(hints)

        # self.set_hint_flag(hint, selected_player)

        return Hint(self.sender, selected_player[0], hint)


if __name__ == '__main__':
    a = {"a": 1, "b": 2}
    print(max(a.items(), key=lambda x: x[1]))
