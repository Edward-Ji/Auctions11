class CompetitorInstance:
    
    def __init__(self):
        # game phase constants
        self.PHASE_1 = "phase_1"
        self.PHASE_2 = "phase_2"
        
        # npc bot stage constants
        self.NPC_LOW_STAGE = 0b00
        self.NPC_MID_STAGE = 0b01
        self.NPC_HGH_STAGE = 0b10
        
        # npc bot bid chance each stage
        self.NPC_BID_PROB = {
            self.NPC_LOW_STAGE: 0.64,
            self.NPC_MID_STAGE: 0.16,
            self.NPC_HGH_STAGE: 0.04
        }
    
    @staticmethod
    def to_unsign(n: int) -> int:
        """
        Converts a signed number to an unsigned one that is proportional to the number's magnitude.
        :param n: signed number
        :return: converted unsigned number
        """
        return 2 * n if n > 0 else -2 * n + 1
    
    @staticmethod
    def from_unsign(n: int) -> int:
        """
        Converts a unsigned number back to the original signed number.
        :param n: converted unsigned number
        :return: signed number
        """
        return (-1) ** (n % 2) * (n // 2)
    
    def encode(self, tv: int) -> list[int]:
        """
        Encode the true value using the unsign method above and convert to base code_base
        :param tv: true value
        :return: a sequence of base code_case numbers
        """
        diff = tv - self.params["meanTrueValue"]
        unsigned = self.to_unsign(diff)
        code = []
        while unsigned != 0:
            code.append(unsigned % self.code_base)
            unsigned //= self.code_base
        if len(code) < self.max_code_size:
            code.append(self.max_bid_inc)
        return code
    
    def code_complete(self, code: list[int]) -> bool:
        """
        Check if a code sequence is complete for decoding.
        :param code: a sequence of base code_base numbers
        :return: if the code is complete
        """
        return len(code) == self.max_code_size or \
               self.max_bid_inc in code
    
    def decode(self, code: list[int]) -> int:
        """
        Decode the sequence of base code_base numbers back to the actual true value
        :param code: a sequence of base code_base numbers
        :return: true value
        """
        unsigned = 0
        if code[-1] == self.max_bid_inc:
            code.pop(-1)
        for i, x in enumerate(code):
            unsigned += x * self.code_base ** i
        diff = self.from_unsign(unsigned)
        return self.params["meanTrueValue"] + diff
    
    def norm_prob(self, x: float) -> float:
        """
        Return cumulative density function of x.
        :param x: test statistic (i.e. z-score)
        :return: CDF(x)
        """
        q = self.engine.math.erf(x / self.engine.math.sqrt(2.0))
        return (1.0 + q) / 2.0
    
    def npc_stage(self, last_bid: int) -> int:
        """
        Return the NPC bid stage code.
        :param last_bid: the previous bid made
        :return: the stage bit code
        """
        if last_bid > self.params["meanTrueValue"] * 3 / 4:
            return self.NPC_HGH_STAGE
        if last_bid > self.params["meanTrueValue"] / 4:
            return self.NPC_MID_STAGE
        else:
            return self.NPC_LOW_STAGE

    @property
    def raw_true_value(self):
        """
        The actual true value. It is 0 when the true value can't be determined.
        :return: true value
        """
        if self.params["phase"] == self.PHASE_1:
            if self.true_value:
                return self.true_value
            else:
                return self.shared_true_value
        else:
            if self.team_bots & self.unique_bots:
                if self.index not in self.unique_bots:
                    return self.true_value
                else:
                    return self.shared_true_value
            else:
                return 0
    
    @property
    def real_true_value(self):
        """
        Returns the actual value of that auction with knowledge penalty. Same as `raw_true_value`, it is 0 when not 
        known.
        :return: true value with knowledge penalty
        """
        if self.params["phase"] == self.PHASE_1:
            if self.true_value:
                return self.true_value - self.params["knowledgePenalty"]
            else:
                return self.shared_true_value
        else:
            if self.team_bots & self.unique_bots:
                if self.index not in self.unique_bots:
                    return self.true_value - self.params["knowledgePenalty"]
                else:
                    return self.shared_true_value
            else:
                return 0
    
    def find_team_bots(self) -> None:
        if self.team_bots or self.round_no < 1:
            return
        
        for i, history in enumerate(self.bid_history):
            if len(history) == sum(self.round_counts[i]) and \
                    all(map(lambda x: x % self.team_prime == 0, history)):
                self.team_bots.add(i)
        if len(self.team_bots) != 3:
            self.team_bots.clear()
        else:
            self.engine.print(f"Bot {self.index} found team bots {self.team_bots}.")
    
    def find_enemy_bots(self) -> None:
        self.enemy_bots.clear()
        
        p_values = [1 for _ in range(self.params["numPlayers"])]
        for i in range(self.params["numPlayers"]):
            if self.params["phase"] == self.PHASE_1:
                if any(map(lambda bid: bid > self.max_bid_inc, self.inc_history[i])):
                    p_values[i] = 0
                    continue
            else:
                if any(map(lambda bid: bid > 232, self.inc_history[i])):
                    p_values[i] = 0
                    continue
            
            # perform hypothesis testing on bidding probability
            test_stats = []  # store test statistic and weight (w = 1/sd)
            for stage, prob in self.NPC_BID_PROB.items():
                if self.round_counts[i][stage] == 0:
                    continue
                x = self.bid_counts[i][stage] / self.round_counts[i][stage]
                sd = self.engine.math.sqrt(prob * (1 - prob) / self.round_counts[i][stage])
                test_stats.append(((x - prob) / sd, 1 / sd))
            # preform additional testing on bidding increment in phase 2 games
            if self.params["phase"] == self.PHASE_2 and sum(self.bid_counts[i]) != 0:
                x = sum(self.inc_history[i]) / sum(self.bid_counts[i]) / self.params["minimumBid"]
                sd = 7 / self.engine.math.sqrt(sum(self.bid_counts[i]))
                test_stats.append((x / sd, 1 / sd))
            # merge z-scores using weighted method
            if not test_stats:
                continue
            final_test_stat = sum(map(lambda ts: ts[0] * ts[1], test_stats)) / \
                self.engine.math.sqrt(sum(map(lambda ts: ts[1] ** 2, test_stats)))
            # obtain p-value with normal distribution probability function
            p_values[i] = 2 * self.norm_prob(-abs(final_test_stat))

        threshold = 9e-3 if self.params["phase"] == self.PHASE_1 else 5e-3
        enemy_bots = set(range(self.params["numPlayers"])) - self.team_bots
        enemy_bots = filter(lambda i: p_values[i] < threshold, enemy_bots)
        self.enemy_bots = set(sorted(enemy_bots, key=lambda i: p_values[i])[:6])
        
        self.enemy_bots -= self.team_bots
    
    def find_team_unique(self, final=False) -> None:
        # requires team bots found
        if not self.team_bots:
            return
        
        # find team unique bot if not found
        codes = self.codes
        team_bots = sorted(self.team_bots)
        if final:
            codes[team_bots.index(self.index)] = self.true_value_code
            
        if not self.team_bots & self.unique_bots:
            for c1, c2, c3 in zip(*codes):
                if c2 == c3 != c1:
                    self.unique_bots.add(team_bots[0])
                elif c1 == c3 != c2:
                    self.unique_bots.add(team_bots[1])
                elif c1 == c2 != c3:
                    self.unique_bots.add(team_bots[2])

        if self.params["phase"] == self.PHASE_2 and \
                self.team_bots & self.unique_bots and \
                self.index in self.unique_bots:
            self.pending_bids.clear()
        
        # find shared true value upon team unique bot found
        if self.team_bots & self.unique_bots and not self.real_true_value:
            if self.params["phase"] == self.PHASE_1:
                team_true_value_bot, = self.team_bots & self.unique_bots
            else:
                team_true_value_bot, _ = self.team_bots - self.unique_bots
            true_value_code = codes[team_bots.index(team_true_value_bot)]
            if self.code_complete(true_value_code):
                self.shared_true_value = self.decode(true_value_code)
                self.engine.print(f"Bot {self.index} found shared true value {self.shared_true_value}.")
    
    def find_unique_bots(self) -> None:
        # guarantee team unique bot report even if it's not found
        if not self.team_bots & self.unique_bots:
            if self.team_bots:
                team_bots = sorted(self.team_bots)
                self.unique_bots.add(team_bots[team_bots.index(self.index) - 1])
        
        # otherwise guess enemy unique bots
        else:
            last_bids = map(lambda l: l[-1] if l else 0, self.bid_history)
            diffs = [self.raw_true_value - bid for bid in last_bids]
            if self.raw_true_value:
                if self.params["phase"] == self.PHASE_1:
                    ordered = sorted(filter(lambda i: diffs[i] >= 50, self.enemy_bots),
                                     key=lambda i: diffs[i])
                    ordered += sorted(self.enemy_bots, key=lambda i: diffs[i])
                else:
                    ordered = sorted(filter(lambda i: 0 <= diffs[i] < 50, self.enemy_bots),
                                     key=lambda i: diffs[i])
                    ordered += sorted(self.enemy_bots, key=lambda i: abs(diffs[i]))
            else:
                ordered = list(self.enemy_bots)
                self.engine.random.shuffle(ordered)
            
            if len(ordered) < 5:
                all_bots = set(range(self.params["numPlayers"]))
                ordered += sorted(all_bots - self.team_bots - set(ordered), key=lambda i: diffs[i])
            
            team_unique_bot, = self.team_bots & self.unique_bots
            team_other_bot, _ = sorted(self.team_bots - self.unique_bots)
            if self.index == team_unique_bot:
                self.unique_bots.remove(self.index)  # do not self report
                self.unique_bots |= set(ordered[2:5])
            elif self.index == team_other_bot:
                self.unique_bots |= set(ordered[:2])
    
    def reset(self) -> None:
        # initialise classification of unique bots
        self.unique_bots: set[int] = set()
        self.codes: list[list[int]] = [[] for _ in range(3)]
        
        self.start_index = self.params["bidOrder"][self.auction_no]
        
        self.stage = self.NPC_LOW_STAGE
        self.last_bid = 1
        self.last_bid_index = self.start_index
        self.last_turn_index = self.start_index
        
        self.round_no = 0
        self.round_history = [False for _ in range(self.params["numPlayers"])]
    
    def hard_reset(self) -> None:
        # initialise classification of team bots and enemy bots
        self.team_bots: set[int] = set()
        self.enemy_bots: set[int] = set()
        
        # reset bidding counts history
        counts: list[int] = [0 for _ in range(3)]
        self.bid_counts: list[list[int]] = [counts.copy() for _ in range(self.params["numPlayers"])]
        self.round_counts: list[list[int]] = [counts.copy() for _ in range(self.params["numPlayers"])]
        self.bid_history: list[list[int]] = [[] for _ in range(self.params["numPlayers"])]
        self.inc_history: list[list[int]] = [[] for _ in range(self.params["numPlayers"])]
        self.codes: list[list[int]] = [[] for _ in range(3)]
    
    def register_turn(self, index) -> None:
        skip_index = self.last_turn_index
        while skip_index != index:
            skip_index += 1
            if skip_index == self.params["numPlayers"]:
                skip_index = 0
            self.round_counts[skip_index][self.stage] += 1
            self.round_history[skip_index] = False
            if skip_index == self.start_index:
                self.round_no += 1
        self.last_turn_index = index
    
    @property
    def must_bid(self) -> bool:
        """
        Returns a bool that indicate if this bot must bid. According to the rules, an auction is won by the last bidder
        if the number of passes equal to the number of players. This checks if passing this turn could result in that
        many passes.
        :return: whether this bot must bid
        """
        if not self.team_bots:
            return False
        
        index = (self.index + 1) % self.params["numPlayers"]
        bid_count = 0
        while index not in self.team_bots - self.unique_bots:
            bid_count += self.round_history[index]
            index = (index + 1) % self.params["numPlayers"]
        return bid_count == sum(self.round_history)
    
    def bid_by_inc(self, inc: int, check: bool=True) -> None:
        """
        Bid the least bid amount increased by a given number. When check enabled, only bid if the value is less than
        the true value (including knowledge penalty). If the ture value is unknown use the minimum threshold of true
        value distribution (mean - 1 * std).
        :param inc: the amount of increase from the least bid that can be made
        :param check: whether to check if this bot is going to overbid
        """
        least_bid = self.last_bid + self.params["minimumBid"]
        bid = least_bid + inc
        
        true_value = self.real_true_value
        if true_value == 0:
            true_value = self.params["meanTrueValue"] - self.params["stddevTrueValue"]
            
        if bid <= true_value or not check:
            self.engine.makeBid(least_bid + inc)
        elif least_bid <= true_value:
            self.engine.makeBid(true_value)
    
    def request_swap(self) -> None:
        """
        Request to swap to the first bidding position.
        """
        if not self.team_bots:
            return
        
        team_bots = sorted(self.team_bots)
        self.engine.swapTo((self.params["bidOrder"][self.auction_no + 1] + team_bots.index(self.index) + 1) %
                           self.params["numPlayers"])
    
    def onGameStart(self, engine, params: dict[str, int]):
        self.engine = engine
        self.params = params
        
        self.auction_no = 0
        
        # the prime number for team bot verification
        self.team_prime = 13 if self.params["phase"] == self.PHASE_1 else 61
        
        # the maximum information that can be shared under npc bid limit
        self.max_bid_inc = 15 if self.params["phase"] == self.PHASE_1 else 63
        self.code_base = self.max_bid_inc - 1
        
        # the maximum number of rounds needed to share complete information
        math = self.engine.math
        self.max_code_size = math.ceil(math.log(2 * self.params["stddevTrueValue"]) / math.log(self.code_base))
    
    def onAuctionStart(self, index: int, true_value: int):
        if self.auction_no == 0 or self.params["phase"] == self.PHASE_2:
            # initialise bid history before the first auction
            # information lost in phase 2 games due to swapping
            self.hard_reset()
        self.reset()
        
        self.index = index
        self.true_value = true_value if true_value != -1 else 0
        self.shared_true_value = 0
        
        if self.true_value:
            self.true_value_code = self.encode(self.true_value)
        else:
            self.true_value_code = [self.max_bid_inc]
        self.pending_bids = self.true_value_code.copy()
        self.engine.print(f"Bot {self.index} pending bids {self.pending_bids}")
    
    def onBidMade(self, index: int, bid: int):
        self.stage = self.npc_stage(self.last_bid)
        
        self.register_turn(index)
        
        self.bid_counts[index][self.stage] += 1
        
        self.bid_history[index].append(bid)
        inc = bid - self.last_bid - self.params["minimumBid"]
        self.inc_history[index].append(inc)
        if self.team_bots and index in self.team_bots:
            code = self.codes[sorted(self.team_bots).index(index)]
            if not self.code_complete(code):
                code.append(inc)
        
        self.last_bid = bid
        self.last_bid_index = index
        
        self.round_history[index] = True
        
        self.find_team_bots()
        self.find_team_unique()
    
    def onMyTurn(self, _):
        self.stage = self.npc_stage(self.last_bid)
        
        self.register_turn(self.index)
        
        least_bid = self.last_bid + self.params["minimumBid"]
        below_npc_rate = self.bid_counts[self.index][self.stage] < \
            self.round_counts[self.index][self.stage] * self.NPC_BID_PROB[self.stage]
        
        # stage 1 : team bot verification
        if not self.team_bots:
            inc = self.team_prime - least_bid % self.team_prime if least_bid % self.team_prime else 0
            self.bid_by_inc(inc)
        
        # stage 2: share true values and compare
        elif self.pending_bids:
            self.bid_by_inc(self.pending_bids.pop(0))
        
        # stage 3: imitate npc bidding behaviour
        elif below_npc_rate:
            if self.params["phase"] == self.PHASE_1:
                self.bid_by_inc(self.engine.random.randint(0, self.max_bid_inc))
            else:
                self.bid_by_inc(abs(self.engine.random.gauss(0, self.max_bid_inc)))
        
        # stage 4: bid if someone else is taking
        elif self.must_bid and self.index not in self.unique_bots:
            self.bid_by_inc(0)
    
    def onAuctionEnd(self):
        self.engine.print(f"Bot {self.index} given true value {self.true_value}")
        self.engine.print(f"Bot {self.index} real true value {self.real_true_value}")
        
        self.find_team_bots()
        self.find_enemy_bots()
        self.find_team_unique(final=True)
        self.find_unique_bots()
        
        # generate and report bot classifications
        team_bots = list(sorted(self.team_bots))
        enemy_bots = list(sorted(self.enemy_bots))
        unique_bots = list(sorted(self.unique_bots))
        
        self.engine.reportTeams(team_bots, enemy_bots, unique_bots)
        self.engine.print(f"Bot {self.index} report {team_bots, enemy_bots, unique_bots}")
        
        # request swap
        if self.params["phase"] == self.PHASE_2 and self.auction_no != 4:
            self.request_swap()
        
        self.auction_no += 1
