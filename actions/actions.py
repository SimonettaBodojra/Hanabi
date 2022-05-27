from abc import ABC, abstractmethod
from GameData import ClientHintData, ClientPlayerPlayCardRequest, ClientPlayerDiscardCardRequest
from game import Player
from client_state.card_info import Color, Value


class Action(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def serialize(self) -> bytes:
        pass


class Hint(Action):
    def __init__(self, agent_name: str, destination_player: Player, hint):
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
        self.game_data = ClientHintData(sender=agent_name, destination=destination_player.name,
                                                        type=hint_type, value=value)

    def serialize(self) -> bytes:
        return self.game_data.serialize()


class PlayCard(Action):
    def __init__(self, agent_name: str, card_index: int):
        super().__init__()
        self.game_data = ClientPlayerPlayCardRequest(sender=agent_name, handCardOrdered=card_index)

    def serialize(self) -> bytes:
        return self.game_data.serialize()


class DiscardCard(Action):
    def __init__(self, agent_name: str, card_index: int):
        super().__init__()
        self.game_data = ClientPlayerDiscardCardRequest(sender=agent_name, handCardOrdered=card_index)

    def serialize(self) -> bytes:
        return self.game_data.serialize()


if __name__ == '__main__':
    Hint(agent_name="Agent1", destination_player=Player(name="CIAO"), hint=Color.WHITE)
    Hint(agent_name="Agent1", destination_player=Player(name="CIAO"), hint=Value.TWO)
