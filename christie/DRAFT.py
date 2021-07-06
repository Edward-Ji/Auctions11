class CompetitorInstance():
    def __init__(self):
        # initialize personal variables
        pass
    
    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine=engine
        # gameParameters: A dictionary containing a variety of game parameters
        self.gameParameters = gameParameters
    
    def onAuctionStart(self, index, trueValue):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value 
        self.index = index
        self.trueValue = trueValue
        self.last_bid = 0
        self.last_bid_index = 0
        self.teambots = set(range(self.gameParameters["numPlayers"]))
    

    def onBidMade(self, whoMadeBid, howMuch):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was
        
        # check whether bid is a multiple of 7 -- teammate
        if howMuch % 7 != 0 and whoMadeBid in self.teambots:
            self.teambots.remove(whoMadeBid)
        
        # save latest bid information
        self.last_bid = howMuch
        self.last_bid_index = whoMadeBid


    def onMyTurn(self,lastBid):
        if self.trueValue == -1:
            true_value = self.gameParameters["meanTrueValue"]/4
        else:
            true_value = self.trueValue - self.gameParameters["knowledgePenalty"]
            
        least_bid = lastBid + self.gameParameters["minimumBid"]

        
        if least_bid % 7 != 0:
            least_bid += (7 - least_bid % 7)
        
        
        if least_bid < true_value:
            self.engine.makeBid(least_bid)
            self.last_bid = least_bid
            
    def onAuctionEnd(self):
        # Now is the time to report team members, or do any cleanup.
        #check whether team_bot has length more than 3
        
        if len(self.teambots) <= 3:
            team_bots = list(self.teambots)
        else:
            team_bots = []
        
        opponent_bots = []
        true_value_bots = []

        self.engine.reportTeams(team_bots, opponent_bots, true_value_bots)