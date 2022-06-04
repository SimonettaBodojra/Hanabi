from actions.rules import *


class RuleManager:
    USEFULNESS_THRESHOLD = 0.6
    DISPENSABLE_THRESHOLD = 0.2
    NEXT_PLAYER = False

    def __init__(self, state):
        self.state = state
        self.rules_dict = {
            1: PlaySafeCard(state),
            2: PlayUsefulCard(state, usefulness_threshold=self.USEFULNESS_THRESHOLD),
            3: PlayJustHinted(state, usefulness_threshold=self.USEFULNESS_THRESHOLD),
            4: PlayRandomCard(state),
            5: PlayJustHintedIfSingle(state),
            6: DiscardUselessCard(state),
            7: DiscardRandomCard(state),
            8: DiscardDispensableCard(state, dispensable_threshold=self.DISPENSABLE_THRESHOLD),
            9: DiscardJustHinted(state, dispensable_threshold=self.DISPENSABLE_THRESHOLD),
            10: DiscardOldestUnhintedCard(state),
            11: DiscardOldest(state),
            12: HintOnes(state, next_player=self.NEXT_PLAYER),
            13: HintPlayableCard(state, next_player=self.NEXT_PLAYER),
            14: HintMostInformation(state, next_player=self.NEXT_PLAYER),
            15: HintRandom(state, self.NEXT_PLAYER),
            16: HintUsefulCard(state, self.NEXT_PLAYER),
            17: HintFullKnowledge(state, "playable", self.NEXT_PLAYER),
            18: HintFullKnowledge(state, "useless", self.NEXT_PLAYER),
            19: HintFullKnowledge(state, "useful", self.NEXT_PLAYER),
            20: HintCritical(state, next_player=self.NEXT_PLAYER),
            21: HintUnknown(state, next_player=self.NEXT_PLAYER),
            22: PlayUsefulCard(state, usefulness_threshold=.5),
            23: DiscardDispensableCard(state, dispensable_threshold=.3)

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
            lambda state: PlayJustHintedIfSingle(state),
            lambda state: PlayUsefulCard(state, usefulness_threshold=self.USEFULNESS_THRESHOLD),
            lambda state: HintPlayableCard(state, next_player=False),
            lambda state: HintMostInformation(state, next_player=False),
            lambda state: HintFullKnowledge(state, next_player=False),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=self.DISPENSABLE_THRESHOLD),
            lambda state: DiscardRandomCard(state)
        ]

    def get_my_strategy2(self):
        return [
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.9),
            lambda state: HintMostInformation(state),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.7),
            lambda state: HintPlayableCard(state),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.5),
            lambda state: DiscardUselessCard(state),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.5),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.3),
            lambda state: DiscardOldest(state),
            lambda state: HintUnknown(state),
        ]

    def get_my_2players_strategy(self):

        # Se si hanno delle certezze sulle carte le si gioca o le si scarta

        #PlaySafeCard, DiscardUseless
        ruleset = [self.rules_dict[1], self.rules_dict[6]]

        # Quando si arriva a terminare gli hint in due,
        # se nessuno ha alcune carte playable in mano si tende a dare un hint appena possibile
        # e a scartare soltant

        # Se hai usato al massimo 6 blue tokens
        if self.state.used_blue_token < 6:

            # HintFullKnowledgePlayable (se gli è già stato dato un hint, completalo)
            ruleset.append(self.rules_dict[17])

            # HintFullKnowledgeUseless
            ruleset.append(self.rules_dict[18])

            # HintPlayable
            ruleset.append(self.rules_dict[13])

            #HintFullKnowledgeUseful
            ruleset.append(self.rules_dict[19])

            # HintUseful
            ruleset.append(self.rules_dict[16])

            # HintMostInfo
            ruleset.append(self.rules_dict[14])

        elif self.state.used_blue_token == 7:

            #L'ultimo hint che gli do è che almeno non scarti una carta critica

            #HintCritical
            ruleset.append(self.rules_dict[20])

        #PlayJustHintedIfSingle
        ruleset.append(self.rules_dict[5])

        #PlayUseful
        ruleset.append(self.rules_dict[2])

        #DiscardDispensable
        ruleset.append(self.rules_dict[10])

        #DiscardOldestUnhinted
        ruleset.append(self.rules_dict[10])

        if self.state.used_red_token == 0:

            #Rischio di giocare una carta con una threshold più bassa
            #I cinque non arriveranno mai alla threshold 0.6,
            # al masssimo arriveranno a 0.5

            ruleset.append(self.rules_dict[22])

            #Altrimenti posso dare un ultimo indizio

            # HintFullKnowledgePlayable (se gli è già stato dato un hint, completalo)
            ruleset.append(self.rules_dict[17])

            # HintFullKnowledgeUseless
            ruleset.append(self.rules_dict[18])

            #HintFullKnowledgeUseful
            ruleset.append(self.rules_dict[19])

            # HintMostInfo
            ruleset.append(self.rules_dict[14])

            #DiscardOldestUnhinted
            ruleset.append(self.rules_dict[10])



        return ruleset


    def get_population_strategy(self):
        pass




