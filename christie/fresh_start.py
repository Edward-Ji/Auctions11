class CompetitorInstance:
    
    def __init__(self):
        # game phase constants
        self.PHASE_1 = "phase_1"
        self.PHASE_2 = "phase_2"
        
        # npc bot stage constants
        self.NPC_LOW_STAGE = 0b10
        self.NPC_MID_STAGE = 0b01
        self.NPC_HGH_STAGE = 0b11
        
        # team bot prime multiplier test
        self.TEAM_PRIME = 17
        
        # npc bot bid chance each stage
        self.NPC_BID_PROB = {
            self.NPC_LOW_STAGE: 0.64,
            self.NPC_MID_STAGE: 0.16,
            self.NPC_HGH_STAGE: 0.04
        }
        
    @staticmethod
    def z_score(x, mean, sd):
        return (x - mean) / sd

    def norm_prob(self, x):
        q = self.engine.math.erf(x / self.engine.math.sqrt(2.0))
        return (1.0 + q) / 2.0
    
    def npc_stage(self, last_bid):
        if last_bid > self.params["meanTrueValue"] * 3 / 4:
            return self.NPC_HGH_STAGE
        if last_bid > self.params["meanTrueValue"] / 4:
            return self.NPC_MID_STAGE
        else:
            return self.NPC_LOW_STAGE
        
    def predict_team(self):
        pass
    
    def predict_enemy(self):
        pass
    
    def predict_unique(self):
        pass
    
    # reset report records
    def reset_history(self):
        # reset classification of bots
        self.team_bots = []
        self.enemy_bots = []
        self.unique_bots = []
        
        # reset bidding counts history
        count_list = [0 for _ in range(self.params["numPlayers"])]
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
    
    # called when game starts
    def onGameStart(self, engine, params):
        self.engine = engine
        self.params = params
        
        self.auction_no = 0
        
        self.reset_history()
    
    # called when auction starts
    def onAuctionStart(self, index, true_value):
        self.index = index
        self.true_value = true_value
        
        self.stage = self.NPC_LOW_STAGE
        self.last_bid = 1
        self.last_bid_index = self.params[""]
        
        self.auction_no += 1

        self.round_no = 0
        self.round_history = []
        
        # information lost in phase 2 games due to swapping
        if self.params["phase"] == self.PHASE_2:
            self.reset_history()
    
    # called when any player makes bid
    def onBidMade(self, idx, bid):
        stage = self.npc_stage(self.last_bid)
        
        self.stage_bid_counts[stage][idx] += 1
        
        self.last_bid = bid
        self.round_history.append(idx)
    
    # called upon my turn to make bid
    def onMyTurn(self, last_bid):
        stage = self.npc_stage(self.last_bid)
        
        self.stage_round_counts[stage] += 1
        self.round_no += 1
        
        self.round_history.clear()
    
    # called when auction ends, also time to report
    def onAuctionEnd(self):
        self.engine.reportTeams(self.team_bots, self.enemy_bots, self.unique_bots)
        
        
