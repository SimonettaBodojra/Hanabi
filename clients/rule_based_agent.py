import GameData
from client_state.agent_state import AgentState


class RuleBasedAgent:

    def __init__(self, game_state: GameData.ServerGameStateData, agent_name: str = "Agent1"):
        self.agent_name: str = agent_name
