import GameData
from agent_state import AgentState


class Agent:

    def __init__(self, game_state: GameData.ServerGameStateData, agent_name: str = "Agent1"):
        self.agent_name: str = agent_name
