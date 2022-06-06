# Computational Intelligence 2021-2022

Exam of computational intelligence 2021 - 2022. It requires teaching the client to play the game of Hanabi (rules can be found [here](https://www.spillehulen.dk/media/102616/hanabi-card-game-rules.pdf)).

## Server

The server accepts passing objects provided in GameData.py back and forth to the clients.
Each object has a ```serialize()``` and a ```deserialize(data: str)``` method that must be used to pass the data between server and client.

Watch out! I'd suggest to keep everything in the same folder, since serialization looks dependent on the import path (thanks Paolo Rabino for letting me know).

Server closes when no client is connected.

To start the server:

```bash
python server.py <minNumPlayers>
```

Arguments:

+ minNumPlayers, __optional__: game does not start until a minimum number of player has been reached. Default = 2


Commands for server:

+ exit: exit from the server

## Client

To start the server:

```bash
python client.py <IP> <port> <PlayerName>
```

Arguments:

+ IP: IP address of the server (for localhost: 127.0.0.1)
+ port: server TCP port (default: 1024)
+ PlayerName: the name of the player

Commands for client:

+ exit: exit from the game
+ ready: set your status to ready (lobby only)
+ show: show cards
+ hint \<type> \<destinatary>:
  + type: 'color' or 'value'
  + destinatary: name of the person you want to ask the hint to
+ discard \<num>: discard the card *num* (\[0-4]) from your hand

## Rule Based Agent

To start the server:

```bash
python rule_based_agent.py <NumAgents> <NumGames> <StepByStep>
```

Arguments:

+ NumAgents: number of agents (integer value, max=5 min=2)
+ NumGames: number of games that can be consequently played (integer value)
+ StepByStep: for debug purposes, it can stop the game between agents at each round (bool value)

## Best Results

| NumAgents | Score | Strategy                                   | Score File Reference     |
|-----------|-------|--------------------------------------------|--------------------------|
| 2         | 17.09 | most_info_strategy                         | scores/2 players/game_7  |
| 3         | 16.24 | two_player_strategy1 (next_player = False) | scores/3 players/game_2  |
| 4         | 15.55 | most_info_strategy (next_player = False)   | scores/4 players/game_8  |
| 5         | 13.85 | most_info_strategy2 (next_player False)    | scores/4 players/game_11 |

