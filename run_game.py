from gameEngine import GameEngine, NPCRandomBot

# import your bots here
import importlib
import random

botsToRun = {
    "christie.cooperate": random.randint(2, 3),
    "christie.hypo_testing": random.randint(2, 3),
    "christie.hypo_testing2": random.randint(2, 3)
}
botsToRun["NPC"] = 10 - sum(botsToRun.values())

engine = GameEngine()

engine.gameParameters["auctionsCount"] = 1

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
    print(index, player["instance"], "True Value" if player["knowsTrue"] else '')