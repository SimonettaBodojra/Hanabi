from abc import ABC, abstractmethod
from client_state.agent_state import AgentState
from actions import Action, Hint, PlayCard, DiscardCard
from itertools import compress

class Rule(ABC):

    @staticmethod
    @abstractmethod
    def rule_to_action(self, state: AgentState) -> Action:
        raise NotImplementedError

# PLAY RULES

class PlaySafeCart(Rule):
    # Play a card which is guaranteed that is playlable
    # A card is playable when it can be placed in one of the stacks and we have full knowledge
    def rule_to_action(self, state: AgentState) -> Action:
        # [True, False..] is is playable or not
        playable_cards_bool = [state.is_card_playable(hidden_card) for hidden_card in state.hand]

        playable_cards = [item for count, item in state.hand if playable_cards_bool[count]]

       # if sum(playable_cards_bool) > 1:
            #Choose the one that makes another player's card playable
