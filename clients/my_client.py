from abc import ABC, abstractmethod
import logging
import socket
import GameData
from constants import HOST, PORT, DATASIZE
from sys import stdout
from enum import Enum
from actions.actions import Action, Hint, PlayCard, DiscardCard
from typing import Tuple

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


class Client(ABC):
    """Classe base per interagire col server"""

    def __init__(self, player_name: str, host: str = HOST, port: int = PORT):
        self.player_name = player_name
        self.host = host
        self.port = port
        self.socket = None
        self.state = ClientState.NOT_CONNECTED
        self.current_player = None
        self.__connect_to_server()

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

        self.state = ClientState.CONNECTED
        logging.info(
            f"Connection accepted by the server. {self.player_name} is waiting in lobby"
        )

    def __read_response(self) -> GameData.ServerToClientData:
        """Legge il prossimo messaggio del server"""
        data = self.socket.recv(DATASIZE)
        response = GameData.GameData.deserialize(data)
        return response

    def __send_request(self, request: GameData.ClientToServerData):
        """Invia una richiesta generica al server"""
        self.socket.send(request.serialize())
        return

    def __send_game_status_request(self):
        """Richiede lo stato del gioco al server"""
        request = GameData.ClientGetGameStateRequest(self.player_name)
        self.__send_request(request)
        return

    def send_start(self):
        if self.state != ClientState.CONNECTED:
            raise RuntimeError("You must be connected")

        start_request = GameData.ClientPlayerStartRequest(self.player_name)
        self.__send_request(start_request)

        response = self.__read_response()

        if type(response) is not GameData.ServerPlayerStartRequestAccepted:
            raise ConnectionError("Invalid response received on Start request.")

        self.state = ClientState.LOBBY
        logging.info(
            msg=f"{self.player_name} - Players ready: {response.acceptedStartRequests}/{response.connectedPlayers}"
        )

    def wait_start(self):
        if self.state != ClientState.LOBBY:
            raise RuntimeError("You are not in lobby")

        # read until it's a ServerStart
        while self.state == ClientState.LOBBY:
            response = self.__read_response()
            if type(response) is GameData.ServerStartGameData:
                ready_request = GameData.ClientPlayerReadyData(self.player_name)
                self.__send_request(ready_request)
                self.state = ClientState.IN_GAME

                state = self.fetch_state()
                self._init_game_state(state)

                logging.debug(msg=f"{self.player_name} - ready request sent")
                logging.info(msg=f"{self.player_name} - Game started")
            logging.debug(msg=f"response received: {response} of type {type(response)}")
        return True

    @abstractmethod
    def _init_game_state(self, state: GameData.ServerGameStateData):
        self.current_player = state.currentPlayer

    def run(self):
        if self.state != ClientState.IN_GAME:
            return

        while self.state == ClientState.IN_GAME:
            # Se è il mio turno allora trovo la best action e la gioco
            if self.current_player == self.player_name:
                action = self.get_next_action()
                action_result, new_state = self.__play_action(action)
            else:
                action_result, new_state = self.fetch_action_result()
            if action_result is not None:  # possbible for game over
                self.update_state_with_action(action_result, new_state)
            stdout.flush()
        return

    @abstractmethod
    def get_next_action(self) -> Action:
        """Sarà implementata dai singoli agenti che erediteranno da questa classe"""
        raise NotImplementedError

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
            logging.info("The game is over.")
            self.state = ClientState.GAME_OVER
            return None, None

        logging.debug(response)
        new_state = self.fetch_state()
        played_action = self.build_action_from_server_response(response, new_state)
        return played_action, new_state

    def fetch_state(self) -> GameData.ServerGameStateData:
        """Recupera lo stato del gioco"""
        if self.state != ClientState.IN_GAME:
            raise RuntimeError("You must be in game")

        self.__send_game_status_request()
        response = self.__read_response()
        while not type(response) is GameData.ServerGameStateData:
            response = self.__read_response()

        return response
        # raise ValueError(f"Invalid state received. {response} received.")

    @abstractmethod
    def update_state_with_action(
        self,
        played_action: GameData.ServerToClientData,
        new_state: GameData.ServerGameStateData,
    ):
        """Update current player"""
        self.current_player = new_state.currentPlayer
        return

    def build_action_from_server_response(
        self, data: GameData.ServerToClientData, new_state: GameData.ServerToClientData
    ):
        """Ricrea l'action di un altro giocatore a partire dai dati ritornati dal server e aggiorna lo stato"""

        if type(data) is GameData.ServerHintData:
            return Hint.from_server_hint(data)

        elif type(data) is GameData.ServerActionValid:
            # a discard has been performed :^)
            # include the drawn card in the created Discard action
            sender = data.lastPlayer
            card_index = data.cardHandIndex
            card_discarded = data.card
            card_drawn = self.get_new_sender_card(sender, new_state, card_index)
            return Discard(sender, card_index, card_discarded, card_drawn)

        elif type(data) is GameData.ServerPlayerMoveOk:
            # a card has been successfully played :^D
            sender = data.lastPlayer
            card_index = data.cardHandIndex
            real_card = data.card
            card_drawn = self.get_new_sender_card(sender, new_state, card_index)
            result = Play.GOOD_MOVE
            return Play(sender, card_index, real_card, card_drawn, result)

        elif type(data) is GameData.ServerPlayerThunderStrike:
            # a card has been unsuccessfully played :^@
            sender = data.lastPlayer
            card_index = data.cardHandIndex
            real_card = data.card
            card_drawn = self.get_new_sender_card(sender, new_state, card_index)
            result = Play.THUNDERSTRIKE
            return Play(sender, card_index, real_card, card_drawn, result)
        else:
            raise ValueError("Invalid action response: {data}")

    def get_new_sender_card(
        self, sender: str, new_state: GameData.ServerGameStateData, card_index: int
    ):
        if sender == self.player_name:
            return UnknownCard()
        for p in new_state.players:
            if p.name == sender:
                return p.hand[-1]  # drawn card are appended to the player hand
        raise ValueError("Unable to fetch the new drawn card!!")
