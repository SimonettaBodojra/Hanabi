from abc import ABC, abstractmethod

import GameData
from GameData import ClientHintData, ClientPlayerPlayCardRequest, ClientPlayerDiscardCardRequest
from game import Player
from client_state.card_info import Color, Value


class Action(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def client_to_server_data(self) -> GameData.ClientToServerData:
        pass


class Hint(Action):
    def __init__(self, source_player: str, destination_player: str, hint, positions = None):
        super().__init__()

        if type(hint) is Color:
            hint_type = "color"
            value = str(hint)
        elif type(hint) is Value:
            hint_type = "value"
            value = hint.value
        else:
            raise Exception("Unknown hint type")

        print(f"TYPE: {hint_type}")
        print(f"VALUE: {value}")
        self.game_data = ClientHintData(sender=source_player, destination=destination_player,
                                        type=hint_type, value=value)

    def client_to_server_data(self) -> GameData.ClientToServerData:
        return self.game_data

    @staticmethod
    def from_server_hint(server_hint: GameData.ServerHintData):
        if server_hint.type == "color":
            hint = Color.fromStringColor(server_hint.value)
        else:
            hint = Value(server_hint.value)
        return Hint(server_hint.source, server_hint.destination, hint, server_hint.positions)


class PlayCard(Action):
    def __init__(self, agent_name: str, card_index: int):
        super().__init__()
        self.game_data = ClientPlayerPlayCardRequest(sender=agent_name, handCardOrdered=card_index)

    def client_to_server_data(self) -> GameData.ClientToServerData:
        return self.game_data


class DiscardCard(Action):
    def __init__(self, agent_name: str, card_index: int):
        super().__init__()
        self.game_data = ClientPlayerDiscardCardRequest(sender=agent_name, handCardOrdered=card_index)

    def client_to_server_data(self) -> GameData.ClientToServerData:
        return self.game_data


if __name__ == '__main__':
    Hint(source_player="Agent1", destination_player=Player(name="CIAO"), hint=Color.WHITE)
    Hint(source_player="Agent1", destination_player=Player(name="CIAO"), hint=Value.TWO)
