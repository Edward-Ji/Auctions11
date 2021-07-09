class CompetitorInstance:
    def __init__(self):
        # initialize constant variables
        self.STAGE_PROB = {
            "low": 0.64,
            "mid": 0.16,
            "high": 0.04
        }
        self.PRIME = 13
    
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
        
        count_list = [0] * self.gameParameters["numPlayers"]
        self.bid_counts = {"low": count_list.copy(),
                           "mid": count_list.copy(),
                           "high": count_list.copy(),
                           "total": count_list.copy()}
        self.stage_counts = {"low": 0, "mid": 0, "high": 0}
    
    def onAuctionStart(self, index, trueValue):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value
        self.index = index
        self.true_value = trueValue
        self.last_bid = 1
        self.last_bid_index = 11
        self.n_rounds = 0
        
        self.bid_history = [[] for _ in range(self.gameParameters["numPlayers"])]

        self.team_bots = []
        self.opponent_bots = []
        self.true_value_bots = []
        
    def onBidMade(self, whoMadeBid, howMuch):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was
        
        # count towards bid count (used to identify npc)
        self.bid_counts[self.stage(self.last_bid)][whoMadeBid] += 1
        self.bid_counts["total"][whoMadeBid] += 1
        
        # count towards seven multiplier count (teammate signature)
        self.bid_history[whoMadeBid].append((self.last_bid, howMuch))
        
        # save latest bid information
        self.last_bid = howMuch
        self.last_bid_index = whoMadeBid
    
    def onMyTurn(self, lastBid):
        # increment round count
        self.stage_counts[self.stage(lastBid)] += 1
        self.n_rounds += 1
        
        # predict teammate after round 3
        self.predict_team()
        
        if self.true_value == -1:
            self.predict_true_value()
        true_value = self.true_value
        
        least_bid = lastBid + self.gameParameters["minimumBid"]
        
        if self.n_rounds <= 2:
            # first two rounds broadcast teammate signature
            if least_bid % self.PRIME != 0:
                least_bid += self.PRIME - least_bid % self.PRIME
            true_value = self.gameParameters["meanTrueValue"]
        else:
            # third round onwards true value bot broadcast ture value
            if self.true_value != -1:
                if self.n_rounds == 3:
                    least_bid = least_bid + self.true_value % 100
                elif self.n_rounds == 4:
                    least_bid = least_bid + self.true_value // 100
                    self.true_value = -1
        
        if len(self.true_value_bots) == 0:
            true_value = self.gameParameters["meanTrueValue"] - self.gameParameters["stddevTrueValue"]
            
        if least_bid <= true_value:
            if true_value - least_bid < self.gameParameters["minimumBid"] * self.gameParameters["numPlayers"]:
                least_bid = true_value - self.gameParameters["minimumBid"] + 1
            self.engine.makeBid(least_bid)
            
    def predict_team(self):
        if self.n_rounds != 3:
            return
    
        # calculate teammate bots
        team_bots = []
        for i, bid_history in enumerate(self.bid_history):
            if len(bid_history) >= 2 and \
                    self.bid_history[i][0][1] % self.PRIME == 0 and \
                    self.bid_history[i][1][1] % self.PRIME == 0:
                team_bots.append(i)
        
        self.team_bots = team_bots
    
    def predict_opponent(self):
        num_players = self.gameParameters["numPlayers"]
        sqrt = self.engine.math.sqrt
        
        # calculate opponent bots
        npc_probs = []
        for i in range(num_players):
            p_values = []
            # hypothesis test bid probability for each stage
            for stage, prob in self.STAGE_PROB.items():
                if self.stage_counts[stage] == 0:
                    continue
                x = self.bid_counts[stage][i] / self.stage_counts[stage]
                mean = prob
                sd = sqrt(prob * (1 - prob) / self.stage_counts[stage])
                test_stat = (x - mean) / sd
                p_values.append(2 * self.prob_norm(-abs(test_stat)))
            npc_probs.append(p_values)
        opponent_bots = list(filter(lambda i: any(map(lambda p: p < 0.0008, npc_probs[i])),
                                    range(num_players)))
        
        self.opponent_bots = opponent_bots
        
        self.engine.print(f"\nNPC prob - Index: {self.index}\n" +
                          "\n".join(map(str, enumerate(npc_probs))))
    
    def predict_true_value(self):
        if self.n_rounds != 5:
            return

        minimum_bid = self.gameParameters["minimumBid"]
        
        for i in self.team_bots:
            if i != self.index and len(self.bid_history[i]) >= 4:
                self.true_value = 0
                last_bid, made_bid = self.bid_history[i][2]
                self.true_value += made_bid - last_bid - minimum_bid
                last_bid, made_bid = self.bid_history[i][3]
                self.true_value += (made_bid - last_bid - minimum_bid) * 100
                self.true_value_bots = [i]

        self.engine.print(f"\nBid history - Index: {self.index}\n" +
                          "\n".join(map(str, enumerate(self.bid_history))))
    
    def onAuctionEnd(self):
        self.predict_opponent()
        
        self.engine.reportTeams(self.team_bots, self.opponent_bots, self.true_value_bots)
