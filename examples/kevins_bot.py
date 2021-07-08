class CompetitorInstance():

    def __init__(self):
        # initialize personal variables
        self.trueValue = -1
        self.index = -1
        self.players = {}
        self.teamPos = []
        self.opponentPos = []
        self.trueValuePos = []
        self.teamCount = 1
        self.llBid = [-1, -1]
        self.percentage = 0.125
        self.bidCount = 0
        self.currentRound = 0
        self.bidPlayers = []

    def calculateBid(self, lastBid):
        bid = lastBid + int(lastBid * self.percentage) + self.gameParameters["minimumBid"] + 3
        return bid

    def checkBid(self, lastBid, percentage):
        if (lastBid - self.gameParameters["minimumBid"] - 3 - int(self.llBid[1] * self.percentage)) == self.llBid[1]:
            return True
        else:
            return False

    def checkTeam(self, index):
        if self.players[index] == 2:
            self.teamPos.append(index)
            self.teamCount += 1

    def checkOpponent(self):
        stopped = 0
        for each in range(len(self.bidPlayers)):
            if self.bidPlayers[each] < self.currentRound-2:
                if (each not in self.opponentPos) and (each not in self.teamPos):
                    self.opponentPos.append(each)
                stopped += 1
        if stopped >= 3:
            return True
        return False

    def extractTrueValue(self, lastBid):
        self.trueValue = (lastBid - self.gameParameters["minimumBid"] - 3 - self.llBid[1] * (1 + self.percentage)) / (self.percentage + self.percentage ** 2)

    def makeBid(self, bid):
        self.engine.makeBid(bid)
        self.bidPlayers[self.index] += 1
        self.bidCount += 1

    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine = engine
        # gameParameters: A dictionary containing a variety of game parameters
        self.gameParameters = gameParameters
        for i in range(self.gameParameters["numPlayers"]):
            self.bidPlayers.append(0)

    def onAuctionStart(self, index, trueValue):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value
        self.llBid = [-1, -1]
        self.trueValue = -1
        if trueValue != -1:
            self.trueValue = trueValue
        self.index = index
        self.currentRound += 1
        self.bidPlayers = []
        for i in range(self.gameParameters["numPlayers"]):
            self.bidPlayers.append(0)

    def onBidMade(self, whoMadeBid, howMuch):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was
        self.llBid[1] = self.llBid[0]
        self.llBid[0] = howMuch
        self.bidPlayers[whoMadeBid] += 1
        if whoMadeBid not in self.players:
            self.players[whoMadeBid] = 0
        if self.checkBid(howMuch, self.percentage):
            self.players[whoMadeBid] += 1
        if self.teamCount <= 3:
            self.checkTeam(whoMadeBid)
        if (whoMadeBid in self.teamPos) and (self.players[whoMadeBid] == 3) and (self.trueValue < 0):
            self.extractTrueValue(howMuch)
            self.players[whoMadeBid] = 0

    def onMyTurn(self, lastBid):
        # lastBid is the last bid that was made
        self.currentRound += 1
        if lastBid < self.gameParameters["meanTrueValue"]:
            # But don't bid too high!
            if self.checkOpponent():
                pass
            if self.bidCount < 2:
                self.makeBid(self.calculateBid(lastBid))
            else:
                if self.bidCount == 2:
                    if self.trueValue >= 0:
                        self.makeBid(self.calculateBid(lastBid + self.trueValue * self.percentage))
                    else:
                        self.makeBid(self.calculateBid(lastBid - 1 * self.percentage))
                else:
                    if self.trueValue >= 0:
                        bid = self.calculateBid(lastBid)
                        if bid > self.trueValue:
                            pass
                        else:
                           self.makeBid(bid)
                    else:
                        bid = self.calculateBid(lastBid)
                        if bid > self.gameParameters["meanTrueValue"] - self.gameParameters["stddevTrueValue"]:
                            pass
                        else:
                            self.makeBid(bid)

    def onAuctionEnd(self):
        # Now is the time to report team members, or do any cleanup.
        self.engine.reportTeams(self.teamPos, list(set(self.opponentPos)), self.trueValuePos)
