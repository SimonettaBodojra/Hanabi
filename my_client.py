from abc import ABC, abstractmethod
import logging
import socket
import GameData
from constants import HOST, PORT, DATASIZE
from sys import stdout
from enum import Enum
from actions.actions import Action, HintResult, PlayCardResult, DiscardCardResult
from typing import Tuple
from client_state.player_hand import HiddenCard, ObservableCard
from game import Card

logging.basicConfig(
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
)


class ClientState(Enum):
    NOT_CONNECTED = "NOT CONNECTED"
    CONNECTED = "CONNECTED"
    LOBBY = "LOBBY"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME OVER"

    def __str__(self):
        return self.value


class Client(ABC):
    """Classe base per interagire col server"""

    def __init__(self, player_name: str, host: str = HOST, port: int = PORT, game_number: int = 1):
        self.player_name = player_name
        self.starting_hand_size = None
        self.host = host
        self.port = port
        self.socket = None
        self.client_state = ClientState.NOT_CONNECTED
        self.current_player = None
        self.game_number = game_number
        self.current_game = 0
        self.__connect_to_server()

    def __read_response(self) -> GameData.ServerToClientData:
        """Legge il prossimo messaggio del server"""
        data = self.socket.recv(DATASIZE)
        response = GameData.GameData.deserialize(data)
        return response

    def __send_request(self, request: GameData.ClientToServerData):
        """Invia una richiesta generica al server"""
        self.socket.send(request.serialize())
        return

    def __connect_to_server(self):
        # creo il socket e mi connetto al server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

        # chiedo di entrare in partita
        connection_request = GameData.ClientPlayerAddData(self.player_name)
        self.__send_request(connection_request)

        # aspetto la risposta del server
        response = self.__read_response()
        if type(response) is not GameData.ServerPlayerConnectionOk:
            raise ConnectionError("There was an error while connecting to the server.")

        self.client_state = ClientState.CONNECTED
        logging.info(
            f"Connection accepted by the server. {self.player_name} is waiting in lobby"
        )

    def send_start(self):
        if self.client_state != ClientState.CONNECTED:
            raise RuntimeError("You must be connected")

        start_request = GameData.ClientPlayerStartRequest(self.player_name)
        self.__send_request(start_request)

        response = self.__read_response()

        if type(response) is not GameData.ServerPlayerStartRequestAccepted:
            raise ConnectionError("Invalid response received on Start request.")

        self.client_state = ClientState.LOBBY
        logging.info(
            msg=f"{self.player_name} - Players ready: {response.acceptedStartRequests}/{response.connectedPlayers}"
        )

    def wait_start(self):
        if self.client_state != ClientState.LOBBY:
            raise RuntimeError("You are not in lobby")

        # read until it's a ServerStart
        while self.client_state == ClientState.LOBBY:
            response = self.__read_response()
            if type(response) is GameData.ServerStartGameData:
                ready_request = GameData.ClientPlayerReadyData(self.player_name)
                self.__send_request(ready_request)
                self.client_state = ClientState.PLAYING

                state = self.get_game_status()
                self._init_game_state(state)

                logging.info(msg=f"{self.player_name} - Game started")

    def restart(self):
        if self.client_state != ClientState.GAME_OVER:
            raise RuntimeError("Match is not over yet")

        self.client_state = ClientState.PLAYING

        state = self.get_game_status()
        self._init_game_state(state)

        logging.info(msg=f"{self.player_name} - Game started")

        self.run()

    def run(self):
        if self.client_state != ClientState.PLAYING:
            return

        while self.client_state == ClientState.PLAYING:
            # Se è il mio turno allora trovo la best action e la gioco
            logging.info(f"TURN: {self.current_player}")
            if self.current_player == self.player_name:
                action = self.get_next_action()
                action_result, new_state = self.__play_action(action)
                logging.info(f"{self.player_name}: {action_result}")

            else:
                logging.info(f"WAITING OTHER PLAYERS ACTION")
                action_result, new_state = self.fetch_action_result()
                logging.info(f"{self.player_name}: {action_result}")

            if action_result is not None:  # se è None allora è game-over
                self.update_state_with_action(action_result, new_state)

            elif self.client_state == ClientState.GAME_OVER and self.current_game + 1 < self.game_number:
                self.current_game += 1
                stdout.flush()
                self.restart()

            stdout.flush()

    def __play_action(self, action: Action):
        # Invio la request corrispondente all'azione al server
        self.__send_request(action.client_to_server_data())
        # Aspetto il risultato
        action_result, new_state = self.fetch_action_result()
        return action_result, new_state

    def fetch_action_result(self) -> Tuple[Action or None, GameData.ServerGameStateData or None]:
        """Ritorna la tupla (Action, GameData.ServerGameStateData)
        dove il primo è la action giocata e il secondo è il nuovo stato del gioco

        # when a player perform an action the server will:
        # - send ServerInvalidAction or ServerInvalidData
        #  if the action/data is not valid, but only to the current user
        # (for all kind of moves)
        # - hint: send ServerHintData
        # - discard: send ServerActionValid
        #   requires a state fetch
        # - play: send either ServerPlayerThunderStrike, ServerPlayerMoveOk
        #   requires a state fetch
        """
        response = self.__read_response()

        if type(response) is GameData.ServerActionInvalid:
            raise ValueError(f"ActionInvalid received: {response.message}")
        elif type(response) is GameData.ServerInvalidDataReceived:
            raise ValueError(f"InvalidData received: {response.data}")
        elif type(response) is GameData.ServerGameOver:
            self.client_state = ClientState.GAME_OVER
            self.game_over(response.score)
            return None, None

        new_state = self.get_game_status()
        played_action = self.build_action_from_server_response(response, new_state)
        return played_action, new_state

    def get_game_status(self) -> GameData.ServerGameStateData:
        """Recupera lo stato del gioco"""
        if self.client_state != ClientState.PLAYING:
            raise RuntimeError("You must be in game")

        request = GameData.ClientGetGameStateRequest(self.player_name)
        self.__send_request(request)

        response = self.__read_response()
        while not type(response) is GameData.ServerGameStateData:
            response = self.__read_response()

        return response

    def build_action_from_server_response(
        self, data: GameData.ServerToClientData, new_state: GameData.ServerToClientData
    ):
        """Ricrea l'action di un altro giocatore a partire dai dati ritornati dal server e aggiorna lo stato"""

        if type(data) is GameData.ServerHintData:
            return HintResult(data)

        elif type(data) is GameData.ServerActionValid:
            # a discard has been performed :^)
            # include the drawn card in the created Discard action
            sender = data.lastPlayer
            card_drawn = self.draw_card(sender, new_state)
            return DiscardCardResult(data, card_drawn)

        elif type(data) is GameData.ServerPlayerMoveOk:
            # a card has been successfully played :^D
            sender = data.lastPlayer
            card_drawn = self.draw_card(sender, new_state)
            return PlayCardResult(data, card_drawn)

        elif type(data) is GameData.ServerPlayerThunderStrike:
            # La carta giocata non viene aggiunta ai firework
            sender = data.lastPlayer
            card_drawn = self.draw_card(sender, new_state)
            return PlayCardResult(data, card_drawn)
        else:
            raise ValueError(f"Invalid action response: {data}")

    def draw_card(
        self, sender: str, new_state: GameData.ServerGameStateData
    ) -> HiddenCard or ObservableCard:

        hand_size = min([new_state.handSize] + [len(player.hand) for player in new_state.players if player.name != self.player_name])
        new_state.handSize = hand_size

        """Trova la carta pescata dal giocatore in questione"""
        if sender == self.player_name:
            if self.starting_hand_size == hand_size:
                return HiddenCard(is_new=True)
            else:
                return None
        else:
            for p in new_state.players:
                if p.name == sender:
                    # le carte pescate vengono sempre appese alla fine della lista
                    if hand_size != self.starting_hand_size:
                        return None

                    card: Card = p.hand[-1]
                    return ObservableCard(card.value, card.color)
        raise ValueError("Player not found")

    @abstractmethod
    def _init_game_state(self, state: GameData.ServerGameStateData):
        self.current_player = state.currentPlayer
        self.starting_hand_size = state.handSize

    @abstractmethod
    def update_state_with_action(
            self,
            played_action: Action,
            new_state: GameData.ServerGameStateData,
    ):
        """Update current player"""
        self.current_player = new_state.currentPlayer
        return

    @abstractmethod
    def get_next_action(self) -> Action:
        """Sarà implementata dai singoli agenti che erediteranno da questa classe"""
        raise NotImplementedError

    @abstractmethod
    def game_over(self, score: int):
        logging.info("Game Over!")
