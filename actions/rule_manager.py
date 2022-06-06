from actions.rules import *


class RuleManager:

    def __init__(self, state):
        self.state = state

    def two_player_strategy1(self):
        next_player = False
        return [
            lambda state: PlaySafeCard(state),
            lambda state: DiscardUselessCard(state),
            lambda state: HintPlayableCard(state, next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.7),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.7),
            lambda state: HintFullKnowledge(state, check="playable", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="useful", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="dispensable", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="useless", next_player=next_player),
            lambda state: HintMostInformation(state, next_player=next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.5),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.5),
            lambda state: HintUnknown(state, next_player=next_player),
            lambda state: DiscardOldestUnhintedCard(state),
            lambda state: DiscardRandomCard(state)
        ]

    def two_player_strategy2(self):
        next_player = False
        return [
            lambda state: PlaySafeCard(state),
            lambda state: DiscardUselessCard(state),
            lambda state: HintPlayableCard(state, next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.8),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.8),
            lambda state: HintFullKnowledge(state, check="playable", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="useful", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="dispensable", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="useless", next_player=next_player),
            lambda state: HintMostInformation(state, next_player=next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.4),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.4),
            lambda state: DiscardOldestUnhintedCard(state),
            lambda state: HintUnknown(state, next_player=next_player),
            lambda state: DiscardRandomCard(state)
        ]

    def just_hinted_strategy(self):
        next_player = False
        return [
            lambda state: PlaySafeCard(state),
            lambda state: DiscardUselessCard(state),
            lambda state: HintPlayableCard(state, next_player),
            lambda state: PlayJustHintedIfSingle(state, usefulness_threshold=0.6),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.8),
            lambda state: HintFullKnowledge(state, check="playable", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="useful", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="dispensable", next_player=next_player),
            lambda state: HintFullKnowledge(state, check="useless", next_player=next_player),
            lambda state: HintCritical(state, next_player=next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.4),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.4),
            lambda state: DiscardOldestUnhintedCard(state),
            lambda state: HintUnknown(state, next_player=next_player),
            lambda state: DiscardRandomCard(state)
        ]

    def my_if_strategy(self):

        next_player = True

        # Se si hanno delle certezze sulle carte le si gioca o le si scarta
        ruleset = [lambda state: PlaySafeCard(state),
                   lambda state: DiscardUselessCard(state)]

        # Quando si arriva a terminare gli hint in due,
        # se nessuno ha alcune carte playable in mano si tende a dare un hint appena possibile
        # e a scartare soltant

        # Se hai usato al massimo 6 blue tokens
        if self.state.used_blue_token < 6:

            # HintFullKnowledgePlayable (se gli è già stato dato un hint, completalo)
            ruleset.append(lambda state: HintFullKnowledge(state, check="playable", next_player=next_player))

            # HintFullKnowledgeUseless
            ruleset.append(lambda state: HintFullKnowledge(state, check="useless", next_player=next_player))

            # HintPlayable
            ruleset.append(lambda state: HintPlayableCard(state, next_player))

            #HintFullKnowledgeUseful
            ruleset.append(lambda state: HintFullKnowledge(state, check="useful", next_player=next_player))

            # HintUseful
            ruleset.append(lambda state: HintUsefulCard(state, next_player))

            # HintMostInfo
            ruleset.append(lambda state: HintMostInformation(state, next_player))

        elif self.state.used_blue_token == 7:

            #L'ultimo hint che gli do è che almeno non scarti una carta critica

            #HintCritical
            ruleset.append(lambda state: HintCritical(state, next_player))

        #PlayJustHintedIfSingle
        ruleset.append(lambda state: PlayJustHintedIfSingle(state, usefulness_threshold=0.6))

        #PlayUseful
        ruleset.append(lambda state: PlayUsefulCard(state, usefulness_threshold=0.6))

        #DiscardDispensable
        ruleset.append(lambda state: DiscardDispensableCard(state, dispensable_threshold=0.8))

        #DiscardOldestUnhinted
        ruleset.append(lambda state: DiscardOldestUnhintedCard(state))

        if self.state.used_red_token == 0:

            #Rischio di giocare una carta con una threshold più bassa
            #I cinque non arriveranno mai alla threshold 0.6,
            # al masssimo arriveranno a 0.5

            ruleset.append(lambda state: PlayUsefulCard(state, usefulness_threshold=0.5))

        # Altrimenti posso dare un ultimo indizio

        # HintFullKnowledgePlayable (se gli è già stato dato un hint, completalo)
        ruleset.append(lambda state: HintFullKnowledge(state, check="playable", next_player=next_player))

        # HintFullKnowledgeUseless
        ruleset.append(lambda state: HintFullKnowledge(state, check="useless", next_player=next_player))

        # HintPlayable
        ruleset.append(lambda state: HintPlayableCard(state, next_player))

        # HintFullKnowledgeUseful
        ruleset.append(lambda state: HintFullKnowledge(state, check="useful", next_player=next_player))

        # HintUseful
        ruleset.append(lambda state: HintUsefulCard(state, next_player))

        # HintMostInfo
        ruleset.append(lambda state: HintMostInformation(state, next_player))

        # DiscardOldestUnhinted
        ruleset.append(lambda state: DiscardOldestUnhintedCard(state))

        return ruleset

    def most_info_strategy(self):

        next_player = False

        return [
            lambda state: PlaySafeCard(state),
            lambda state: DiscardUselessCard(state),
            lambda state: HintPlayableCard(state, next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.7),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.7),
            lambda state: HintMostInformation(state, next_player=next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.4),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.5),
            lambda state: DiscardOldestUnhintedCard(state),
            lambda state: HintUnknown(state, next_player=next_player),
            lambda state: DiscardRandomCard(state)
        ]

    def most_info_strategy2(self):

        next_player = False

        ruleset = [
            lambda state: PlaySafeCard(state),
            lambda state: DiscardUselessCard(state),
            lambda state: HintPlayableCard(state, next_player),
            lambda state: PlayUsefulCard(state, usefulness_threshold=0.7),
            lambda state: DiscardDispensableCard(state, dispensable_threshold=0.7)]

        if self.state.used_blue_token > 4:
            ruleset.append(lambda state: HintFullKnowledge(state, check="playable", next_player=next_player))
            ruleset.append(lambda state: HintFullKnowledge(state, check="useless", next_player=next_player))

        ruleset.extend([lambda state: HintMostInformation(state, next_player=next_player),
                        lambda state: PlayUsefulCard(state, usefulness_threshold=0.4),
                        lambda state: DiscardDispensableCard(state, dispensable_threshold=0.5),
                        lambda state: DiscardOldestUnhintedCard(state),
                        lambda state: HintUnknown(state, next_player=next_player),
                        lambda state: DiscardRandomCard(state)])

        return ruleset
