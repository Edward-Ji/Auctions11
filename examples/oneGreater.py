class CompetitorInstance():
    def __init__(self):
        pass
    
    def onGameStart(self, engine, gameParameters):
        self.engine=engine
        self.gameParameters = gameParameters
    
    def onAuctionStart(self, index, trueValue):
        self.my_last_bid = 0

    def onBidMade(self, whoMadeBid, howMuch):
        pass

    def onMyTurn(self,lastBid):
        if lastBid < self.gameParameters["meanTrueValue"] / 4:
            self.engine.makeBid(int(self.gameParameters["meanTrueValue"] / 4 + 8))
        if lastBid != self.my_last_bid:
            self.my_last_bid = lastBid + 11
            self.engine.makeBid(self.my_last_bid)

    def onAuctionEnd(self):
        pass