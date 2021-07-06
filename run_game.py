from gameEngine import GameEngine, NPCRandomBot

# import your bots here
import importlib

botsToRun = {
    "examples.randomBidder": 3,
    "christie.DRAFT": 3,
    "examples.oneGreater": 3,
    "NPC": 3
}

engine = GameEngine()

engine.gameParameters["auctionsCount"] = 5

# Warning: Timeouts are not enforced locally - so if you have an infinite loop, beware!
for b in botsToRun:
    for i in range(botsToRun[b]):
        if b=="NPC":
            engine.registerBot(NPCRandomBot(), team="NPC")
        else:
            botClass = importlib.import_module(b)
            engine.registerBot(botClass.CompetitorInstance(), team=b)
engine.runGame()

for index, player in enumerate(engine.competitors):
    print(index, player["instance"])
