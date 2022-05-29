import GameData
from actions.actions import Action
from client_state.agent_state import AgentState
from my_client import Client
from actions.actions import PlayCard, Hint, DiscardCard
from threading import Thread


class RuleBasedAgent(Client):

    def __init__(self, player_name: str):
        self.state: None
        super().__init__(player_name)

    def _init_game_state(self, state: GameData.ServerGameStateData):
        self.state = AgentState(state, self.player_name)
        super()._init_game_state(state)

    def update_state_with_action(self, played_action: Action, new_state: GameData.ServerGameStateData):
        self.state.update_state(new_state)
        super().update_state_with_action(played_action, new_state)

    def get_next_action(self) -> Action:
        return PlayCard(self.player_name, 0)


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
    agent_number = 1
    agents_deployers = []
    for a in range(agent_number):
        name = f"Agent_{a}"
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
