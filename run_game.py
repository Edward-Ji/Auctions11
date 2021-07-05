from gameEngine import GameEngine, NPCRandomBot

# import your bots here
import importlib

botsToRun = {
    "christie.test": 2,
    "examples.randomBidder": 2,
    "examples.randomAccuser": 2,
    "NPC": 2
}

engine = GameEngine()

engine.gameParameters["auctionsCount"] = 10

# Warning: Timeouts are not enforced locally - so if you have an infinite loop, beware!
for b in botsToRun:
    if b == "NPC":
        engine.registerBot(NPCRandomBot(), team="NPC")
    else:
        botClass = importlib.import_module(b)
        for i in range(botsToRun[b]):
            engine.registerBot(botClass.CompetitorInstance(), team=b)
engine.runGame()