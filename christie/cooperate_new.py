class CompetitorInstance:
    
    def __init__(self):
        # initialize constant variables
        self.STAGE_PROB = {
            "low": 0.64,
            "mid": 0.16,
            "high": 0.04
        }
        self.PRIME = 17
        self.true_value_PRIME = 19
    
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

        self.team_bots = []
        self.auction_num = 0
    
    def onAuctionStart(self, index, trueValue):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value
        self.index = index
        self.true_value = trueValue
        self.last_bid = 1
        self.last_bid_index = 11
        self.n_rounds = 0
        self.extend_opponents =[]
        self.extend_fake_bot = []
        self.auction_num += 1
        
        self.bid_history = [[] for _ in range(self.gameParameters["numPlayers"])]
        self.last_50_history = [[] for _ in range(self.gameParameters["numPlayers"])]

        self.opponent_bots = []
        self.true_value_bots = []
        self.should_bid = -1
        
            
        if self.gameParameters["phase"] == "phase_2" or (self.gameParameters["phase"] == "phase_1" and len(self.team_bots)>3):
            self.team_bots = []
            self.fake_bot = []
        if self.gameParameters["phase"] == "phase_2":
            count_list = [0] * self.gameParameters["numPlayers"]
            self.bid_counts = {"low": count_list.copy(),
                            "mid": count_list.copy(),
                            "high": count_list.copy(),
                            "total": count_list.copy()}
            self.stage_counts = {"low": 0, "mid": 0, "high": 0}
        
    def onBidMade(self, whoMadeBid, howMuch):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was
        
        # count towards bid count (used to identify npc)
        self.bid_counts[self.stage(self.last_bid)][whoMadeBid] += 1
        self.bid_counts["total"][whoMadeBid] += 1
        
        # count towards seven multiplier count (teammate signature)
        self.bid_history[whoMadeBid].append((self.last_bid, howMuch))

        #used to identify who is likely to not be true value bot
        if self.true_value != -1 and howMuch > self.true_value - self.gameParameters["knowledgePenalty"]:
            self.last_50_history[whoMadeBid].append((self.last_bid, howMuch))
        
        if self.gameParameters["phase"] == "phase_1":
            if howMuch - self.last_bid > 24:
                self.extend_opponents.append(whoMadeBid)
        elif self.gameParameters["phase"] == "phase_2":
            if howMuch - self.last_bid > 240:
                self.extend_fake_bot.append(whoMadeBid)
        
        if self.n_rounds < 3:
            if howMuch % self.PRIME == 0:
                self.team_bots.append(whoMadeBid)
            elif howMuch % self.true_value_PRIME == 0:
                self.true_value_bots.append(whoMadeBid)
                self.team_bots.append(whoMadeBid)
            self.team_bots = list(set(self.team_bots))


        # save latest bid information
        self.last_bid = howMuch
        self.last_bid_index = whoMadeBid



    
    def onMyTurn(self, lastBid):
        # increment round count
        self.stage_counts[self.stage(lastBid)] += 1
        self.n_rounds += 1
        
        # predict teammate after round 3
        self.predict_team()
        # if phase 1, predict true value
        if self.gameParameters["phase"] == "phase_1":
            self.predict_true_value()
        #if phase 2, predict true value
        elif self.gameParameters["phase"] == "phase_2":
            self.predict_true_value()

        true_value = self.true_value 
        
        least_bid = lastBid + self.gameParameters["minimumBid"]
        
        if self.n_rounds <= 2:
            # first two rounds broadcast teammate signature
            if true_value == -1:
                if least_bid % self.PRIME != 0:
                    least_bid += self.PRIME - least_bid % self.PRIME
                true_value = self.gameParameters["meanTrueValue"]
            elif true_value != -1 and least_bid % self.true_value_PRIME != 0:
                least_bid += self.true_value_PRIME - least_bid % self.true_value_PRIME
            
        elif self.n_rounds == 3:
            # third round onwards true value bot broadcast ture value
            if self.true_value != -1:
                least_bid = least_bid + self.true_value % 100
        elif self.n_rounds == 4:
            if self.true_value != -1:
                least_bid = least_bid + self.true_value // 100
                if self.gameParameters["phase"] =="phase_1":
                    self.true_value -= 30
                    #self.gameParameters["knowledgePenalty"]
                    self.true_value_bots = [self.index]

        if least_bid <= true_value:           
            if self.n_rounds <= 4:
                self.engine.makeBid(least_bid)
            elif self.n_rounds > 4:
                if self.gameParameters["phase"] == "phase_1":
                    # if len(self.team_bots) > 0 and self.index not in self. true_value_bots:
                    #     self.team_bots = sorted(self.team_bots)
                    #     if self.index == self.team_bots[0]:
                    #         self.engine.makeBid(least_bid + 20)
                    #     elif len(self.team_bots) > 1:
                    #         if self.index == self.team_bots[1]:
                    #             self.engine.makeBid(least_bid + 20)
                    if self.n_rounds == 5 and least_bid + 20 <= true_value:
                        self.engine.makeBid(least_bid + 20)
                    else:
                        self.engine.makeBid(least_bid)

                            
                elif self.gameParameters["phase"] == "phase_2":
                    if len(self.fake_bot) != 0:
                        if self.index in self.fake_bot:
                            self.engine.makeBid(least_bid)
                    else:
                        self.engine.makeBid(least_bid)


            
    def predict_team(self):
        if self.n_rounds != 3:
            return
    
        # calculate teammate bots
        team_bots = []
        true_value_bot = []

        for i, bid_history in enumerate(self.bid_history):
            if len(bid_history) >= 2 and \
                    self.bid_history[i][0][1] % self.PRIME == 0 and \
                    self.bid_history[i][1][1] % self.PRIME == 0:
                team_bots.append(i)
            elif len(bid_history) >= 2 and \
                    self.bid_history[i][0][1] % self.true_value_PRIME == 0 and \
                    self.bid_history[i][1][1] % self.true_value_PRIME == 0:
                team_bots.append(i)
                true_value_bot.append(i)
        

        self.team_bots = team_bots
        self.true_value_bots = true_value_bot

    
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
        opponent_bots = list(filter(lambda i: any(map(lambda p: p < 0.00085, npc_probs[i])),
                                    range(num_players)))
   
        if self.gameParameters["phase"] == "phase_1":
            self.opponent_bots = opponent_bots + self.extend_opponents
        elif self.gameParameters["phase"] == "phase_2":
            self.opponent_bots = opponent_bots + self.extend_fake_bot
        self.opponent_bots = list(set(self.opponent_bots) - set(self.team_bots))


        # self.engine.print(f"\nNPC prob - Index: {self.index}\n" +
        #                   "\n".join(map(str, enumerate(npc_probs))))
    
    def predict_true_value(self):
        if self.n_rounds != 5:
            return

        minimum_bid = self.gameParameters["minimumBid"]
        if self.gameParameters["phase"] == "phase_2":
            self.true_value_ls = []
            self.true_value_ls.append((self.index, self.true_value))
        
        for i in self.team_bots:
            if i != self.index and len(self.bid_history[i]) >= 4:
                self.true_value = 0
                last_bid, made_bid = self.bid_history[i][2]
                self.true_value += made_bid - last_bid - minimum_bid
                last_bid, made_bid = self.bid_history[i][3]
                self.true_value += (made_bid - last_bid - minimum_bid) * 100
                if self.gameParameters["phase"] == "phase_1":
                    self.true_value_bots = [i]
                elif self.gameParameters["phase"] == "phase_2":
                    self.true_value_ls.append((i, self.true_value))
                    
        if self.gameParameters["phase"] == "phase_2":
            seen = set()
            for p in range(len(self.true_value_ls)):
                if self.true_value_ls[p][1] not in seen:
                    seen.add(self.true_value_ls[p][1])
                else:
                    self.true_value = self.true_value_ls[p][1]
            for z in range(len(self.true_value_ls)):
                if self.true_value_ls[z][1] != self.true_value:
                    self.fake_bot.append(self.true_value_ls[z][0])
            
            if self.index not in self.fake_bot:
                self.true_value -= 50

            

        # self.engine.print(f"\nBid history - Index: {self.index}\n" +
        #                   "\n".join(map(str, enumerate(self.bid_history))))
    
    def onAuctionEnd(self):
        self.predict_opponent()
        self.team_bots = sorted(self.team_bots)
        

        if len(self.true_value_bots) >0:
            if self.index in self.true_value_bots:
                for i in self.extend_opponents:
                    if i not in self.team_bots and len(self.last_50_history[i]) == 0:
                        self.true_value_bots.append(i)
       
        if len(self.true_value_bots) != 0 and len(self.team_bots) != 0 and self.team_bots[0] not in self.true_value_bots:
            if self.index == self.team_bots[0]:
                for i in self.opponent_bots:
                    if i not in self.team_bots and len(self.last_50_history[i]) == 0:
                        self.true_value_bots.append(i)
            elif self.index != self.team_bots[0] and self.index not in self.true_value_bots:
                for i in self.extend_opponents:
                    if i not in self.team_bots and len(self.last_50_history[i]) == 0:
                        self.true_value_bots.append(i)


        elif len(self.true_value_bots) != 0 and len(self.team_bots) > 1 and self.team_bots[0] in self.true_value_bots and self.team_bots[1] not in self.true_value_bots:
            if self.index == self.team_bots[1]:
                for i in self.opponent_bots:
                    if i not in self.team_bots and len(self.last_50_history[i]) == 0:
                        self.true_value_bots.append(i)
            elif self.index != self.team_bots[1] and self.index != self.team_bots[0]:
                for i in self.extend_opponents:
                    if i not in self.team_bots and len(self.last_50_history[i]) == 0:
                        self.true_value_bots.append(i)


        self.true_value_bots = list(set(self.true_value_bots))

        if self.gameParameters["phase"]=="phase_1":
            self.engine.reportTeams(self.team_bots, self.opponent_bots, self.true_value_bots)
            self.engine.print((self.team_bots, self.opponent_bots, self.true_value_bots))

        elif self.gameParameters["phase"]=="phase_2":
            if len(self.fake_bot) != 0 and len(self.team_bots) != 0 and self.team_bots[0] not in self.fake_bot:
                if self.index == self.team_bots[0]:
                    self.fake_bot = [i for i in range(self.gameParameters["numPlayers"])
                                    if i not in self.team_bots and i in self.opponent_bots and len(self.last_50_history[i])!= 0 or i in self.fake_bot]
                elif self.index != self.team_bots[0] and self.index not in self.fake_bot:
                    self.fake_bot = [i for i in range(self.gameParameters["numPlayers"])
                                    if i not in self.team_bots and i in self.opponent_bots and len(self.last_50_history[i])== 0 or i in self.fake_bot]           


                
            elif len(self.fake_bot) != 0 and len(self.team_bots) > 1 and self.team_bots[0] in self.fake_bot and self.team_bots[1] not in self.fake_bot:
                if self.index == self.team_bots[1]:
                    self.fake_bot = [i for i in range(self.gameParameters["numPlayers"])
                                if i not in self.team_bots and i in self.opponent_bots and len(self.last_50_history[i])!= 0 or i in self.fake_bot]
                elif self.index != self.team_bots[1] and self.index != self.team_bots[0]:
                    self.fake_bot = [i for i in range(self.gameParameters["numPlayers"])
                                if i not in self.team_bots and i in self.opponent_bots and len(self.last_50_history[i])== 0 or i in self.fake_bot]

            self.engine.reportTeams(self.team_bots, self.opponent_bots, self.fake_bot)
            self.engine.print((self.team_bots, self.opponent_bots, self.fake_bot))

            # print((self.index, self.fake_bot, self.opponent_bots))
            # print(list(enumerate(self.last_50_history)))
            # print()

