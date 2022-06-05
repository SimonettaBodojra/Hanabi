import logging
from threading import Thread
from actions.actions import *
from actions.rule_manager import RuleManager
from client_state.agent_state import AgentState
from my_client import Client
from typing import List
import sys
import os


class RuleBasedAgent(Client):

    def __init__(self, player_name: str, game_number: int = 1, agent_number: int = 1, step_by_step: bool = False):
        self.state = None
        self.rule_set = None
        self.final_scores = []
        self.step_by_step = step_by_step
        super().__init__(player_name, game_number=game_number, agent_number=agent_number)

    def _init_game_state(self, state: GameData.ServerGameStateData):
        super()._init_game_state(state)
        self.state = AgentState(state, self.player_name)
        logging.debug(self.state)

    def update_state_with_action(self, played_action: Action, new_state: GameData.ServerGameStateData):
        super().update_state_with_action(played_action, new_state)
        self.state.handle_action_result(played_action)
        self.state.update_state(new_state)
        self.state.update_current_belief()

        if hasattr(played_action, "current_player") and played_action.current_player != self.player_name:
            logging.debug(self.state)

    def get_next_action(self) -> Action:
        if self.step_by_step:
            input("PRESS ENTER TO CONTINUE")

        self.rule_set = RuleManager(self.state).two_player_strategy1()
        for rule in self.rule_set:
            rule = rule(self.state)
            action = rule.rule_to_action()
            if action is not None:
                logging.info(f"{self.player_name}: {rule}")
                self.state.is_state_updated = False
                self.state.just_hinted = set()
                return action

    def game_over(self, score: int):
        super().game_over(score)
        self.final_scores.append(score)
        self.state = None
        self.rule_set = None


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
    agent_number = 5
    agents_deployers = []
    game_number = 100
    scores: List[int] = []
    agent_prefix = "agent"
    step_by_step = False

    args = sys.argv
    if len(args) == 2:
        agent_prefix = args[1]
    elif len(args) == 3:
        agent_prefix = args[1]
        step_by_step = True if args[2] == 'true' else False

    for a in range(agent_number):
        name = f"{agent_prefix}{a}"
        agent = RuleBasedAgent(name, game_number, agent_number, step_by_step)
        agents_deployers.append(AgentDeployer(agent))

    for deployer in agents_deployers:
        deployer.enter_game_thread.start()

    for deployer in agents_deployers:
        deployer.enter_game_thread.join()

    for deployer in agents_deployers:
        deployer.start_game_thread.start()

    for deployer in agents_deployers:
        deployer.start_game_thread.join()

    for game in range(game_number):
        scores.append(0)
        for deployer in agents_deployers:
            scores[game] = max(scores[game], deployer.agent.final_scores[game])

    result = f"""

    
************** MATCH WITH {agent_number} players **************
AGENTS:
{[deployer.agent.player_name for deployer in agents_deployers]}

GAME SCORES:
{scores}

AVG SCORE:
{sum(scores) / len(scores)}
    """

    logging.info(f"""

    
{result}
    """)

    path = f"scores/{agent_number} players"
    score_dirs = os.listdir(path)
    if len(score_dirs) == 0:
        new_file = "game_1"
    else:
        last_game_file = score_dirs[-1]
        file_number = int(last_game_file[5:]) + 1
        new_file = f"game_{file_number}"

    with open(f"{path}/{new_file}", "w") as fp:
        fp.write(result)




