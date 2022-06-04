import logging
import random
from threading import Thread, Lock

from actions.actions import *
from actions.rule_manager import RuleManager
from client_state.agent_state import AgentState
from my_client import Client


class RuleBasedAgent(Client):

    def __init__(self, player_name: str):
        self.mutex = Lock()
        self.state: None
        self.rule_set = None
        self.final_score = 0
        super().__init__(player_name)

    def _init_game_state(self, state: GameData.ServerGameStateData):
        self.state = AgentState(state, self.player_name)
        self.rule_set = RuleManager(self.state).get_my_2players_strategy()
        super()._init_game_state(state)

    def update_state_with_action(self, played_action: Action, new_state: GameData.ServerGameStateData):
        super().update_state_with_action(played_action, new_state)
        self.mutex.acquire()
        self.state.handle_action_result(played_action)
        self.state.update_state(new_state)
        self.state.update_current_belief()
        self.mutex.release()

        if hasattr(played_action, "current_player") and played_action.current_player != self.player_name:
            logging.debug(self.state)


    def get_next_action(self) -> Action:
        self.mutex.acquire()
        for rule in self.rule_set:
            action = rule.rule_to_action()
            if action is not None:
                logging.info(f"{self.player_name}: {rule}")
                self.state.is_state_updated = False
                self.state.just_hinted = set()
                self.mutex.release()
                return action
        self.mutex.release()

    def game_over(self, score: int):
        self.final_score = score
        super().game_over(score)


class AgentDeployer:

    def __init__(self, agent_impl: Client):
        self.agent = agent_impl
        self.enter_game_thread = Thread(target=self.__enter_game)
        self.start_game_thread = Thread(target=self.__start_game)

    def __enter_game(self):
        self.agent.send_start()

    def __start_game(self):
        self.agent.wait_start()
        self.agent.run()


if __name__ == '__main__':
    agent_number = 2
    agents_deployers = []
    game_number = 2
    scores = {}

    for a in range(agent_number):
        name = f"Agent{a}"
        agent = RuleBasedAgent(name)
        agents_deployers.append(AgentDeployer(agent))

    for deployer in agents_deployers:
        deployer.enter_game_thread.start()

    for deployer in agents_deployers:
        deployer.enter_game_thread.join()

    for deployer in agents_deployers:
        deployer.start_game_thread.start()

    for deployer in agents_deployers:
        deployer.start_game_thread.join()

    for deployer in agents_deployers:
        previous_score = scores.get(0, 0)
        if previous_score < deployer.agent.final_score:
            scores[0] = deployer.agent.final_score

    logging.info(f"GAME SCORES:\n{scores}")