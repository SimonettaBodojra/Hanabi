from actions.rules import *


class RuleManager:
    USEFULNESS_THRESHOLD = 0.7
    DISPENSABLE_THRESHOLD = 0.7
    NEXT_PLAYER = True

    def __init__(self):
        self.rules_dict = {
            1: lambda state: PlaySafeCard(state),
            2: lambda state: PlayUsefulCard(state, usefulness_threshold=self.USEFULNESS_THRESHOLD),
            3: lambda state: PlayJustHinted(state, usefulness_threshold=self.USEFULNESS_THRESHOLD),
            4: lambda state: PlayRandomCard(state),
            5: lambda state: DiscardUselessCard(state),
            6: lambda state: DiscardRandomCard(state),
            7: lambda state: DiscardDispensableCard(state, dispensable_threshold=self.DISPENSABLE_THRESHOLD),
            8: lambda state: DiscardJustHinted(state, dispensable_threshold=self.DISPENSABLE_THRESHOLD),
            9: lambda state: DiscardOldestUnhintedCard(state),
            10: lambda state: HintOnes(state, next_player=self.NEXT_PLAYER),
            11: lambda state: HintPlayableCard(state, next_player=self.NEXT_PLAYER),
            12: lambda state: HintMostInformation(state, next_player=self.NEXT_PLAYER),
            13: lambda state: HintRandom(state, self.NEXT_PLAYER),
            14: lambda state: HintUsefulCard(state, self.NEXT_PLAYER),
            15: lambda state: HintFullKnowledge(state, self.NEXT_PLAYER),
            16: lambda state: HintCritical(state, next_player=self.NEXT_PLAYER),
            17: lambda state: HintUnknown(state, next_player=self.NEXT_PLAYER)

        }

    # LEGAL AGENT
    # This agent makes a move at random from the set of legal actions available to it at any given time step.
    def get_legal_random_strategy(self):
        ruleset = [self.rules_dict[13], self.rules_dict[4], self.rules_dict[6]]
        random.shuffle(ruleset)

        return ruleset

    # CAUTIOUS AGENT
    # It features memory of what has been told about his hand and the memory of others
    # It is playing without losing any life
    def get_cautious_strategy(self):
        # PlaySafeCard, DiscardUseless, HintPlayable, HintCritical HintUnknown, DiscardRandom
        ruleset = [self.rules_dict[1], self.rules_dict[5],
                   self.rules_dict[16], self.rules_dict[11],
                   self.rules_dict[14], self.rules_dict[17],
                   self.rules_dict[6]]

        return ruleset

    # CAUTIOUS DETERMINISTIC AGENT:
    # It plays without losing any life and with a deterministic discard final rule
    def get_cautious_deterministic_strategy(self):
        # PlaySafeCard, DiscardUseless, HintPlayable, HintCritical, HintUseful HintUnknown, DiscardRandom
        ruleset = [self.rules_dict[1], self.rules_dict[5],
                   self.rules_dict[16], self.rules_dict[11],
                   self.rules_dict[14], self.rules_dict[17],
                   self.rules_dict[9]]

        return ruleset

    # PDH - PlayDiscardHint
    # It an action priority fixed

    def get_pdh_strategy(self):
        # PlaySafe, PlayUseful, DiscardUseless, DiscardDispensable, HintPlayable, HintMostInformation
        ruleset = [self.rules_dict[1], self.rules_dict[2],
                   self.rules_dict[5], self.rules_dict[7],
                   self.rules_dict[11], self.rules_dict[12]]

        return ruleset

    # Hinting ones at the beginning of the game helps to play faster

    def get_hint_ones_strategy(self):
        # HintOnes, PlaySafe, PlayUseful, DiscardUseless, DiscardDispensable, HintPlayable, HintMostInformation, DiscardRandom
        ruleset = [self.rules_dict[10], self.rules_dict[1],
                   self.rules_dict[2], self.rules_dict[5],
                   self.rules_dict[7], self.rules_dict[11],
                   self.rules_dict[12], self.rules_dict[6]]

        return ruleset

    def get_my_strategy1(self):
        return [
            lambda state: PlaySafeCard(state),
            lambda state: DiscardUselessCard(state),
            lambda state: PlayUsefulCard(state, usefulness_threshold=self.USEFULNESS_THRESHOLD),
            lambda state: HintOnes(state),
            lambda state: HintPlayableCard(state),
            lambda state: HintMostInformation(state),
            lambda state: DiscardOldestUnhintedCard(state),
            lambda state: DiscardRandomCard(state)
        ]

    def get_my_strategy2(self):
        pass

    def get_population_strategy(self):
        pass




