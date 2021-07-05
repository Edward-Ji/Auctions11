class CompetitorInstance:
    
    players = {}
    shared_index_known = -1
    shared_true_value = -1
    
    def __init__(self):
        # initialize personal variables
        self.bid_history = []
    
    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine = engine
        self.gameParameters = gameParameters
    
    def onAuctionStart(self, index, trueValue):
        self.auction_history = []
        
        self.players[index] = self
        
        self.true_value = trueValue
        if trueValue != -1:
            self.shared_index_known = index
            self.shared_true_value = trueValue
    
    def onBidMade(self, whoMadeBid, howMuch):
        self.auction_history.append((whoMadeBid, howMuch))
    
    def onMyTurn(self, lastBid):
        
        if self.shared_true_value != -1:
            true_value = self.shared_true_value
        else:
            true_value = self.gameParameters["meanTrueValue"]
        
        if self.true_value != -1:
            true_value -= self.gameParameters["knowledgePenalty"]
        
        least_bid = lastBid + self.gameParameters["minimumBid"]
        if least_bid < true_value:
            self.engine.makeBid(least_bid)
    
    def onAuctionEnd(self):
        team_bots = list(self.players.keys())
        true_value_bots = [self.shared_index_known] if self.shared_index_known != -1 else []
        self.engine.reportTeams(team_bots, [], true_value_bots)
