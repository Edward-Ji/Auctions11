class CompetitorInstance:

    def prob_norm(self, x):
        q = self.engine.math.erf(x / self.engine.math.sqrt(2.0))
        return (1.0 + q) / 2.0
    
    def onGameStart(self, engine, gameParameters):
        self.engine = engine
        for key, value in gameParameters.items():
            setattr(self, key, value)
        
        self.game_history = []
        self.auction_no = 0
    
    def onAuctionStart(self, index, trueValue):
        self.auction_no += 1
        
        self.round_no = 0
    
    def onBidMade(self, whoMadeBid, howMuch):
        pass
    
    def onMyTurn(self, lastBid):
        self.round_no += 1
    
    def onAuctionEnd(self):
        pass
