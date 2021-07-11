class CompetitorInstance:
    
    def __init__(self):
        # bot classifier bit mask
        self.NPC_BOT = 0b10000
        self.ENEMY_BOT = 0b01000
        self.TEAM_BOT = 0b00100
        self.KNOWN_BOT = 0b00010
        self.DUMB_BOT = 0b00001
        self.OTHER_BOT = self.NPC_BOT | self.ENEMY_BOT
        self.TEAM_KNOWN_BOT = self.TEAM_BOT | self.KNOWN_BOT
        self.TEAM_DUMB_BOT = self.TEAM_BOT | self.DUMB_BOT

        # bot stage bit mask
        self.NPC_LOW_STAGE = 0b10
        self.NPC_MID_STAGE = 0b01
        self.NPC_HGH_STAGE = 0b11
        
        # team bot prime multiplier test
        self.TEAM_PRIME = 13
        
        # npc bot bid chance each stage
        self.NPC_BID_PROB = {
            self.NPC_LOW_STAGE: 0.64,
            self.NPC_MID_STAGE: 0.16,
            self.NPC_HGH_STAGE: 0.04
        }
        
    def z_score(self, x, mean, sd):
        return (x - mean) / sd

    def pnorm(self, x):
        q = self.engine.math.erf(x / self.engine.math.sqrt(2.0))
        return (1.0 + q) / 2.0
    
    def npc_stage(self, bid):
        if bid > self.params["meanTrueValue"] * 3 / 4:
            return self.NPC_HGH_STAGE
        if bid > self.params["meanTrueValue"] / 4:
            return self.NPC_MID_STAGE
        return self.NPC_LOW_STAGE
    
    def classify_bot(self, idx):
        # test team bot pattern
        bot_bit_history = self.auction_history[idx]
        if len(bot_bit_history) >= 2 and \
                bot_bit_history[0] % self.TEAM_PRIME == 0 and \
                bot_bit_history[1] % self.TEAM_PRIME == 0:
            self.guesses[idx] |= self.TEAM_BOT
            if len(bot_bit_history) >= 3:
            
    
        # hypothesis test npc bot bidding probabilities
        pass
    
        return 0
    
    def classify_bots(self):
        team_bots = []
        enemy_bots = []
        known_bots = []
        for i in range(self.params["numPlayers"]):
            guess = self.classify_bot(i)
            if guess & self.TEAM_BOT:
                team_bots.append(i)
            elif guess & self.ENEMY_BOT:
                enemy_bots.append(i)
            elif guess & self.KNOWN_BOT:
                known_bots.append(i)
        return team_bots, enemy_bots, known_bots
    
    def onGameStart(self, engine, gameParameters):
        self.engine = engine
        self.params = gameParameters
        
        # keep number of bids and rounds for npc bid probability hypothesis test
        count_list = [0 for _ in range(10)]
        self.stage_bid_counts = {
            self.NPC_LOW_STAGE: count_list.copy(),
            self.NPC_MID_STAGE: count_list.copy(),
            self.NPC_HGH_STAGE: count_list.copy()
        }
        self.stage_round_counts = {
            self.NPC_LOW_STAGE: 0,
            self.NPC_MID_STAGE: 0,
            self.NPC_HGH_STAGE: 0
        }
        
        self.auction_no = 0
        
        self.guesses = [0 for _ in range(self.params["numPlayers"])]
    
    def onAuctionStart(self, index, true_value):
        self.index = index
        self.true_value = true_value
        
        self.stage = self.NPC_LOW_STAGE
        self.last_bid = 1
        
        self.auction_no += 1
        self.auction_history: list[list[int]] = [[] for _ in range(self.params["numPlayers"])]

        self.round_no = 0
        self.round_history = []
    
    def onBidMade(self, idx, bid):
        stage = self.npc_stage(self.last_bid)
        
        self.stage_bid_counts[stage][idx] += 1
        
        self.last_bid = bid
        self.round_history.append(idx)
        
        self.auction_history[idx].append(bid)
        
        self.classify_bot(idx)
    
    def onMyTurn(self, last_bid):
        stage = self.npc_stage(self.last_bid)
        
        self.stage_round_counts[stage] += 1
        self.round_no += 1
        
        self.round_history.clear()
    
    def onAuctionEnd(self):
        self.engine.reportTeams(*self.classify_bots())
        
        
