from abc import ABC, abstractmethod
from typing import List, Dict

from client_state.agent_state import AgentState
from client_state.card_info import Color, Value
from client_state.player_hand import HiddenCard
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


# non è utile quando si utilizzano le HintRules con next_player a False
class PlayJustHintedIfSingle(Rule):
    def __init__(self, state: AgentState, usefulness_threshold: float = .6):
        self.usefulness_threshold = usefulness_threshold
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_red_token > 1:
            return None

        just_hinted = list(self.state.just_hinted)

        if len(just_hinted) != 1:
            return None

        selected_card_index = just_hinted[0]
        selected_card = self.state.hand[selected_card_index]

        if self.state.check_card_usability(selected_card, "playable"):
            return PlayCard(self.sender, selected_card_index)

        if selected_card.hasColorHint():
            playable_value_of_color = self.state.get_playable_cards().get(selected_card.hint_color)
            if playable_value_of_color is None or selected_card.possible_values[playable_value_of_color] < self.usefulness_threshold:
                return None
        else:
            playable_cards = self.state.get_playable_cards()
            possible_playable_colors = [color for color, value in playable_cards.items() if value == selected_card.hint_value]
            if len(possible_playable_colors) == 0:
                return None

            max_probability = max([prob for color, prob in selected_card.possible_colors.items()])
            if max_probability < self.usefulness_threshold:
                return None

        return PlayCard(self.sender, selected_card_index)


# ------ DISCARD RULES (6) ------

class DiscardUselessCard(Rule):
    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 0:
            return None

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

        if self.state.used_blue_token == 0:
            return None

        random_index = random.choice(range(self.state.hand_card_number))

        return DiscardCard(self.sender, random_index)


class DiscardDispensableCard(Rule):
    def __init__(self, state: AgentState, dispensable_threshold: float):
        super().__init__(state)

        self.dispensable_threshold = dispensable_threshold

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 0:
            return None

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
        if self.state.used_blue_token == 0:
            return None

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
        if self.state.used_blue_token == 0:
            return None

        for count, hidden_card in enumerate(self.state.hand):
            if hidden_card.hint_color is None and hidden_card.hint_color is None:
                break

        return DiscardCard(self.sender, count)


class DiscardOldest(Rule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 0:
            return None
        return DiscardCard(self.sender, 0)


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

            hintable_players_info = [(self.state.player_hands[turn].player_name, self.state.player_hands[turn].hand) for
                                     turn in hintable_players]

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

        selected_player = None
        for player in players:
            card_indexes = [idx for idx, card in enumerate(player[1])
                            if self.state.check_card_usability(card, check,
                                                               useful_threshold=useful_threshold,
                                                               dispensable_threshold=dispensable_threshold)
                            and card.is_hintable()]

            if len(card_indexes) > 0:
                selected_player = player
                break

        if selected_player is None:
            return None, None

        rand_index = random.choice(card_indexes)
        random_card = selected_player[1][rand_index]

        if random_card.is_color_hinted:
            return selected_player, random_card.value
        elif random_card.is_value_hinted:
            return selected_player, random_card.color
        else:
            hints = [random_card.value, random_card.color]
            return selected_player, random.choice(hints)


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

    #ObservableCard è playable se può essere messa su un firework

    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:

        if self.state.used_blue_token == 8:
            return None

        card_indexes = []

        selected_player = None
        for player in self.hintable_players():
            card_indexes = [idx for idx, card in enumerate(player[1])
                            if self.state.check_card_usability(card, "playable")
                            and card.is_hintable()]

            if len(card_indexes) > 0:
                selected_player = player
                break

        if selected_player is None:
            return None

        count_per_color: Dict[Color, int] = {color: 0 for color in Color.getColors()}
        count_per_value: Dict[Value, int] = {value: 0 for value in Value.getValues()}

        for idx in card_indexes:
            card = selected_player[1][idx]
            if not card.is_color_hinted:
                count_per_color[card.color] += 1
            if not card.is_value_hinted:
                count_per_value[card.value] += 1

        for idx in card_indexes:
            card = selected_player[1][idx]
            if not card.is_value_hinted:
                hidden_card = HiddenCard()
                hidden_card.set_hint(card.value)
                if self.state.is_card_playable(hidden_card) or count_per_value[card.value] == 1:
                    return Hint(self.sender, selected_player[0], card.value)

            if not card.is_color_hinted:
                hidden_card = HiddenCard()
                hidden_card.set_hint(card.color)
                if self.state.is_card_playable(hidden_card) or not count_per_color[card.color] == 1:
                    return Hint(self.sender, selected_player[0], card.color)

        max_hint = max(list(count_per_color.items()) + list(count_per_value.items()), key=lambda x: x[1])[0]
        hint = max_hint
        hint_type = type(hint)

        for idx in card_indexes:
            card = selected_player[1][idx]
            if hint_type is Value and card.value == hint and not card.is_value_hinted:
                return Hint(self.sender, selected_player[0], hint)
            elif hint_type is Color and card.color == hint and not card.is_color_hinted:
                return Hint(self.sender, selected_player[0], hint)

        raise RuntimeError("IMPOSSIBLE TO BE HERE")


class HintUsefulCard(HintRule):

    #ObservableCard è useful se in futuro potrà essere messa su un firework
    #Sostanzialmente se non è una carta già posta sullo stack

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

#Observable card che ha solamente uno dei due hint,
#Dandogli un hint la renderebbe coerente con il check svolto

    def __init__(self, state: AgentState, check: str, next_player: bool = True):
        super().__init__(state, next_player)
        self.check = check

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        players = self.hintable_players()
        hintable_card_indexes = []

        selected_player = None

        #Tra tutti i giocatori hintabili seleziono il primo che ha carte con un hint
        for player in players:
            hintable_card_indexes = [idx for idx, card in enumerate(player[1])
                                     if (card.is_value_hinted and not card.is_color_hinted) or
                                     (card.is_color_hinted and not card.is_value_hinted)
                                     if self.state.check_card_usability(card, self.check)]

            if len(hintable_card_indexes) > 0:
                selected_player = player
                break

        if selected_player is None:
            return None

        #Trovato il giocatore che ha delle carte con almeno uno dei due hint
        #che siano o playable o useful, si seleziona con priorità prima la playable

        checked_card = None

        for idx in hintable_card_indexes:
            hintable_card = selected_player[1][idx]
            if self.state.check_card_usability(hintable_card, self.check):
                checked_card = hintable_card
                break

        if checked_card is not None:
            if checked_card.is_color_hinted:
                return Hint(self.sender, selected_player[0], checked_card.value)
            else:
                return Hint(self.sender, selected_player[0], checked_card.color)
        else:
            return None


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

        return Hint(self.sender, max_player[0], max_player[1][0])


class HintCritical(HintRule):

    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        players = self.hintable_players()
        critical_cards = {card for card in self.state.get_critical_cards() if not card.is_value_hinted}

        selected_player = None
        selected_card = None
        for player in players:
            player_cards = set(player[1])
            intersection = critical_cards.intersection(player_cards)
            if len(intersection) != 0:
                selected_player = player
                selected_card = random.choice(list(intersection))
                break

        if selected_player is None:
            return None

        return Hint(self.sender, selected_player[0], selected_card.value)


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

        return Hint(self.sender, selected_player[0], Value.ONE)


class HintUnknown(HintRule):
    def __init__(self, state: AgentState, next_player: bool = True):
        super().__init__(state, next_player)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        players = self.hintable_players()
        selected_player = None
        unhinted_card_idxs = []
        for player in players:
            unhinted_card_idxs = [idx for idx, card in enumerate(player[1]) if not card.is_color_hinted and not card.is_value_hinted]
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
