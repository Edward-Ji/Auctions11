class CompetitorInstance:
    def __init__(self):
        # initialize constant variables
        self.STAGE_PROB = {
            "low": 0.64,
            "mid": 0.16,
            "high": 0.04
        }
    
    def prob_norm(self, x):
        q = self.engine.math.erf(x / self.engine.math.sqrt(2.0))
        return (1.0 + q) / 2.0
    
    def stage(self, value):
        mean = self.gameParameters["meanTrueValue"]
        if value > mean * 3 / 4:
            return "high"
        elif value > mean / 4:
            return "mid"
        else:
            return "low"
    
    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine = engine
        # gameParameters: A dictionary containing a variety of game parameters
        self.gameParameters = gameParameters
        
        self.team_bots = []
        self.opponent_bots = []
        self.true_value_bots = []
    
    def onAuctionStart(self, index, trueValue):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value
        self.index = index
        self.true_value = trueValue
        self.last_bid = 1
        self.last_bid_index = 0
        
        count_list = [0] * self.gameParameters["numPlayers"]
        self.bid_counts = {"low": count_list.copy(),
                           "mid": count_list.copy(),
                           "high": count_list.copy(),
                           "total": count_list.copy()}
        self.seven_mul_counts = count_list.copy()
        
        self.round_counts = {"low": 0, "mid": 0, "high": 0}
    
    def onBidMade(self, whoMadeBid, howMuch):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was
        
        # count towards bid count (used to identify npc)
        self.bid_counts[self.stage(self.last_bid)][whoMadeBid] += 1
        self.bid_counts["total"][whoMadeBid] += 1
        
        # count towards seven multiplier count (teammate signature)
        if howMuch % 7 == 0:
            self.seven_mul_counts[whoMadeBid] += 1
        
        # save latest bid information
        self.last_bid = howMuch
        self.last_bid_index = whoMadeBid
    
    def onMyTurn(self, lastBid):
        # increment round count
        self.round_counts[self.stage(lastBid)] += 1
        
        if self.true_value == -1:
            true_value = self.gameParameters["meanTrueValue"] / 4
        else:
            true_value = self.true_value
        
        least_bid = lastBid + self.gameParameters["minimumBid"]
        
        if least_bid % 7 != 0:
            least_bid += 7 - least_bid % 7
        
        if least_bid <= true_value:
            self.engine.makeBid(least_bid)
            self.last_bid = least_bid
            
    def predict_team(self):
        num_players = self.gameParameters["numPlayers"]
    
        # calculate teammate bots
        team_bots = []
        for i in range(num_players):
            if abs(self.seven_mul_counts[i] - self.bid_counts["total"][i]) <= 1 and \
                    abs(self.bid_counts["low"][i] - self.round_counts["low"]) <= 1:
                team_bots.append(i)
        if len(team_bots) > 3:
            team_bots.clear()

        self.team_bots = team_bots
    
    def predict_opponent(self):
        num_players = self.gameParameters["numPlayers"]
        sqrt = self.engine.math.sqrt
        
        # calculate opponent bots
        npc_probs = []
        for i in range(num_players):
            npc_prob = []
            # hypothesis test bid probability for each stage
            for stage, prob in self.STAGE_PROB.items():
                if self.round_counts[stage] == 0:
                    continue
                x = self.bid_counts[stage][i] / self.round_counts[stage]
                mean = prob
                sd = sqrt(prob * (1 - prob) / self.round_counts[stage])
                test_stat = (x - mean) / sd
                npc_prob.append(abs(self.prob_norm(test_stat) - 0.5))
            npc_probs.append(npc_prob)
        opponent_bots = list(filter(lambda i: any(map(lambda p: p > 0.499, npc_probs[i])),
                                         range(num_players)))
        
        self.opponent_bots = opponent_bots
    
    def predict_tv_bot(self):
        # calculate true value bots
        true_value_bots = [i for i in self.team_bots if
                           self.bid_counts["mid"][i] != 0 or
                           self.bid_counts["high"][i] != 0]
        
        self.true_value_bots = true_value_bots
    
    def onAuctionEnd(self):
        self.predict_team()
        self.predict_opponent()
        self.predict_tv_bot()
        
        self.engine.reportTeams(self.team_bots, self.opponent_bots, self.true_value_bots)
