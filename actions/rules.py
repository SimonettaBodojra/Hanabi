from abc import ABC, abstractmethod
from client_state.agent_state import AgentState
from client_state.player_hand import Hand
from client_state.card_info import Color, Value
from actions import Action, Hint, PlayCard, DiscardCard
import random


class Rule(ABC):

    def __init__(self, state: AgentState):
        self.state = state
        self.sender = self.state.agent_name

    @abstractmethod
    def rule_to_action(self) -> Action:
        raise NotImplementedError


# ------ PLAY RULES (4) ------

class PlaySafeCard(Rule):
    # Play a card which is guaranteed that is playable
    # A card is playable when it can be placed in one of the stacks and we have full knowledge
    # TO_DO: gestire caso in cui ci sono più carte playable

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        # List of the playable cards indexes
        playable_cards_indexes = [count for count, hidden_card in enumerate(self.state.hand)
                                  if self.state.check_card_usability(hidden_card, "playable")]

        return PlayCard(self.sender, playable_cards_indexes[0])


class PlayRandomCard(Rule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        random_index = random.choice(range(self.state.hand_card_number))
        return PlayCard(self.sender, random_index)


class PlayUsefulCard(Rule):
    def __init__(self, state: AgentState, usefulness_threshold: float):
        super().__init__(state)

        self.usefulness_threshold = usefulness_threshold

    def rule_to_action(self) -> Action:
        useful_cards_indexes = [count for count, hidden_card in enumerate(self.state.hand)
                                if self.state.check_card_usability(hidden_card, "useful",
                                                                   useful_threshold=self.usefulness_threshold)]
        return PlayCard(self.sender, useful_cards_indexes[0])


class PlayJustHinted(Rule):

    def __init__(self, state: AgentState, usefulness_threshold: float):
        super().__init__(state)

        self.usefulness_threshold = usefulness_threshold

    def rule_to_action(self) -> Action:
        max_prob = .0
        useful_card_index = 0
        for card_index in self.state.just_hinted:
            curr_card = self.state.hand[card_index]
            _, curr_prob = self.state.get_usefulness_probability(curr_card)
            if max_prob < curr_prob:
                useful_card_index = card_index
                max_prob = curr_prob
        return PlayCard(self.sender, useful_card_index)


# ------ DISCARD RULES (6) ------

class DiscardUselessCard(Rule):
    # Play a card which is guaranteed that is playable
    # A card is playable when it can be placed in one of the stacks and we have full knowledge
    # TO_DO: gestire caso in cui ci sono più carte playable

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        # List of the playable cards indexes
        useless_cards_indexes = [count for count, hidden_card in enumerate(self.state.hand)
                                 if self.state.check_card_usability(hidden_card, "useless")]

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
        dispensable_cards_indexes = [count for count, hidden_card in enumerate(self.state.hand)
                                     if self.state.check_card_usability(hidden_card, "dispensable",
                                                                        dispensable_threshold=self.dispensable_threshold)]
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
            _, curr_prob = self.state.get_dispensable_probability(curr_card)
            if max_prob < curr_prob:
                dispensable_card_index = card_index
                max_prob = curr_prob
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

    def __init__(self, state: AgentState):
        super().__init__(state)

        next_player_turn = (self.state.my_turn + 1) % len(self.state.players_list)
        self.destination_player = self.state.players_list[next_player_turn].name
        self.destination_player_hand = self.state.player_hands[next_player_turn].hand

    @staticmethod
    def __choose_random_hint(destination_player_hand):
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

    def __get_hint(self, check: str, useful_threshold: float = .7, dispensable_threshold: float = .7):
        card_indexes = [idx for idx, card in enumerate(self.destination_player_hand)
                        if self.state.check_card_usability(card, check,
                                                           useful_threshold=useful_threshold,
                                                           dispensable_threshold=dispensable_threshold)]

        if len(card_indexes) == 0:
            return None

        rand_index = random.choice(card_indexes)
        random_card = self.destination_player_hand[rand_index]

        if random_card.is_color_hinted:
            return random_card.value
        elif random_card.is_value_hinted:
            return random_card.color
        else:
            hints = [random_card.value, random_card.color]
            return random.choice(hints)

    def __set_hint_flag(self, hint: Value or Color):

        if type(hint) is Color:
            for card_index in range(len(self.destination_player_hand)):
                card = self.destination_player_hand[card_index]
                if card.color == hint:
                    self.destination_player_hand[card_index].is_color_hinted = True

        elif type(hint) is Value:
            for card_index in range(len(self.destination_player_hand)):
                card = self.destination_player_hand[card_index]
                if card.value == hint:
                    self.destination_player_hand[card_index].is_value_hinted = True

        else:
            raise Exception("Unknown hint type")


class HintRandom(HintRule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        hint, hinted_index = self.__choose_random_hint(self.destination_player_hand)

        self.__set_hint_flag(hint)

        return Hint(self.sender, self.destination_player, hint)


class HintPlayableCard(HintRule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:

        if self.state.used_blue_token == 8:
            return None

        hint = self.__get_hint(check="playable")

        if hint is None:
            return None

        self.__set_hint_flag(hint)

        return Hint(self.sender, self.destination_player, hint)


class HintUsefulCard(HintRule):
    def __init__(self, state: AgentState, usefulness_threshold: float = .7):
        super().__init__(state)

        self.usefulness_threshold = usefulness_threshold

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        hint = self.__get_hint(check="useful", useful_threshold=self.usefulness_threshold)

        if hint is None:
            return None

        self.__set_hint_flag(hint)

        return Hint(self.sender, self.destination_player, hint)


class HintFullKnowledge(HintRule):
    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        hintable_card_indexes = [idx for idx, card in enumerate(self.destination_player_hand)
                                 if (card.is_value_hinted and not card.is_color_hinted) or
                                 (card.is_color_hinted and not card.is_value_hinted)]

        if len(hintable_card_indexes) == 0:
            return None

        rand_hint = random.choice(hintable_card_indexes)
        rand_card = self.destination_player_hand[rand_hint]

        if rand_card.is_color_hinted:
            hint = rand_card.value
        else:
            hint = rand_card.color

        self.__set_hint_flag(hint)

        return Hint(self.sender, self.destination_player, hint)


class HintMostInformation(HintRule):

    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        # TODO: completare

        return Hint(self.sender, self.destination_player, Value.FIVE)


class HintFives(HintRule):
    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        fives_count = len([card.value for card in self.destination_player_hand
                           if card.value == Value.FIVE])

        if fives_count == 0:
            return None

        self.__set_hint_flag(Value.FIVE)

        return Hint(self.sender, self.destination_player, Value.FIVE)


class HintOnes(HintRule):
    def __init__(self, state: AgentState):
        super().__init__(state)

    def rule_to_action(self) -> Action:
        if self.state.used_blue_token == 8:
            return None

        ones_count = len([card.value for card in self.destination_player_hand
                           if card.value == Value.ONE])

        if ones_count == 0:
            return None

        self.__set_hint_flag(Value.ONE)

        return Hint(self.sender, self.destination_player, Value.ONE)
