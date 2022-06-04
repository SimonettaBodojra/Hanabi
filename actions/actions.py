from abc import ABC, abstractmethod

import GameData
from GameData import ClientHintData, ClientPlayerPlayCardRequest, ClientPlayerDiscardCardRequest
from client_state.card_info import Color, Value
from client_state.player_hand import ObservableCard, HiddenCard


class Action(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def client_to_server_data(self) -> GameData.ClientToServerData:
        pass


class Hint(Action):
    def __init__(self, source_player: str, destination_player: str, hint: Color or Value):
        super().__init__()
        self.source_player = source_player
        self.destination_player = destination_player
        self.hint = hint

    def client_to_server_data(self) -> GameData.ClientToServerData:
        if type(self.hint) is Color:
            hint_type = "color"
        elif type(self.hint) is Value:
            hint_type = "value"
        else:
            raise Exception("Unknown hint type")

        return ClientHintData(self.source_player, self.destination_player,
                              hint_type, self.hint.value)

    def __str__(self):
        return f"{self.source_player} hinted {self.destination_player} with {self.hint}"


class HintResult(Hint):

    def __init__(self, server_hint: GameData.ServerHintData):
        if server_hint.type == "color":
            hint = Color(server_hint.value)
        elif server_hint.type == "value":
            hint = Value(server_hint.value)
        else:
            raise RuntimeError("Unknown type")

        self.positions = server_hint.positions
        self.current_player = server_hint.player

        super().__init__(server_hint.source, server_hint.destination, hint)

    def __str__(self):
        return f"{self.source_player} hinted {self.destination_player} with {self.hint} in positions {self.positions}"


class PlayCard(Action):
    def __init__(self, source_player: str, card_index: int):
        super().__init__()
        self.source_player = source_player
        self.card_index = card_index

    def client_to_server_data(self) -> GameData.ClientToServerData:
        return ClientPlayerPlayCardRequest(sender=self.source_player, handCardOrdered=self.card_index)

    def __str__(self):
        return f"{self.source_player} played the card in position {self.card_index}"

class PlayCardResult(PlayCard):

    NICE_MOVE = "🔥"
    BAD_MOVE = "😠"

    def __init__(self,
                 server_play_card_result: GameData.ServerPlayerMoveOk or GameData.ServerPlayerThunderStrike,
                 card_drawn: ObservableCard or HiddenCard
                 ):
        if type(server_play_card_result) is GameData.ServerPlayerMoveOk:
            self.result = self.NICE_MOVE
        elif type(server_play_card_result) is GameData.ServerPlayerThunderStrike:
            self.result = self.BAD_MOVE
        else:
            raise RuntimeError("Unknown server response")

        self.current_player = server_play_card_result.player
        self.played_card = ObservableCard(server_play_card_result.card.value, server_play_card_result.card.color)
        self.hand_size = server_play_card_result.handLength
        self.card_drawn = card_drawn
        super().__init__(server_play_card_result.lastPlayer, server_play_card_result.cardHandIndex)

    def __str__(self):
        return f"{self.result} {self.source_player} played the card {self.played_card}"


class DiscardCard(Action):
    def __init__(self, source_player: str, card_index: int):
        super().__init__()
        self.source_player = source_player
        self.card_index = card_index

    def client_to_server_data(self) -> GameData.ClientToServerData:
        return ClientPlayerDiscardCardRequest(sender=self.source_player, handCardOrdered=self.card_index)

    def __str__(self):
        return f"{self.source_player} discarded the card in position {self.card_index}"


class DiscardCardResult(DiscardCard):
    def __init__(self, server_discard_result: GameData.ServerActionValid, card_drawn: ObservableCard or HiddenCard):
        if server_discard_result.action != "discard":
            raise RuntimeError("Unknown action")

        self.current_player = server_discard_result.player
        self.discarded_card = ObservableCard(server_discard_result.card.value, server_discard_result.card.color)
        self.hand_size = server_discard_result.handLength
        self.card_drawn = card_drawn
        super().__init__(server_discard_result.lastPlayer, server_discard_result.cardHandIndex)

    def __str__(self):
        return f"{self.source_player} discarded the card {self.discarded_card}"
    def __str__(self):
        return f"{self.source_player} discarded the card {self.discarded_card}"
