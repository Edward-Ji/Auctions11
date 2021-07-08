import random   
class CompetitorInstance:
    
    players = []
    shared_true_value = 0
    
    def __init__(self):
        # initialize personal variables
        self.bid_history = []
    
    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine = engine
        self.gameParameters = gameParameters
    
    def onAuctionStart(self, index, trueValue):
        self.opponent_bots = set()
        self.npc_prob = dict(zip(range(self.gameParameters["numPlayers"]),
                                 [1] * self.gameParameters["numPlayers"]))
        self.last_bid = 0
        self.last_bid_index = 0
        
        self.players[index] = self
        
        self.true_value = trueValue
        if trueValue != -1:
            self.shared_index_known = index
            self.shared_true_value = trueValue
    
    def onBidMade(self, whoMadeBid, howMuch):
        # guarantee not bot because increase more than three times minimum increment
        if howMuch - self.last_bid > self.gameParameters["minimumBid"] * 3:
            self.opponent_bots.add(whoMadeBid)
            
        # keep npc probability
        mean_true_value = self.gameParameters["meanTrueValue"]
        num_players = self.gameParameters["numPlayers"]
        # prob: the probability of bidding if it's a bot
        prob = 32 / 50
        if self.last_bid > mean_true_value / 4:
            prob = 16 / 100
        if self.last_bid > mean_true_value * 3 / 4:
            prob = 2 / 50
            
        skipped_players = range(self.last_bid_index,
                                whoMadeBid if whoMadeBid > self.last_bid_index else whoMadeBid + num_players)
        for index in skipped_players:
            self.npc_prob[index % num_players] *= 1 - prob
        self.npc_prob[whoMadeBid] *= prob
        
        # save to latest bid information
        self.last_bid = howMuch
        self.last_bid_index = whoMadeBid
    
    def onMyTurn(self, lastBid):
        if self.shared_true_value != -1:
            true_value = self.shared_true_value
        else:
            true_value = self.gameParameters["meanTrueValue"]
        
        least_bid = lastBid + self.gameParameters["minimumBid"]
        if least_bid < true_value:
            self.engine.makeBid(least_bid)
            self.last_bid = least_bid
    
    def onAuctionEnd(self):
        num_players = self.gameParameters["numPlayers"]
        team_bots = list(self.players.keys())
        opponent_bots = list(self.opponent_bots |
                             set(sorted(self.npc_prob.keys(), key=lambda i: self.npc_prob[i])[:int(num_players / 2)]))
        true_value_bots = [self.shared_index_known] if self.shared_index_known != -1 else []
        self.engine.reportTeams(team_bots, opponent_bots, true_value_bots)
