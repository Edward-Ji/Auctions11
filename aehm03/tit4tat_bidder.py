from math import ceil

from bidder import Bidder


class Tit4TatBidder(Bidder):
    
    def __init__(self, number: int, **options):
        """
        :param number:
        :param options:
            relevant_bids: how many of the opponents' recent bids are considered
            max_amount: threshold for not participating
            lead: the amount of increase to place a bid for win, but does not drain cash
        """
        # default values for options
        self.relevant_bids: int = 5
        self.max_amount: int = 7
        self.lead: int = 2
        super().__init__(number, **options)
        self.n_rounds: int = 0
        self.others_cash: list[int] = []
        self.others_bids: list[list[int]] = [[]]

    def start_game(self, quantity: int, cash: int, n_bidders: int):
        super().start_game(quantity, cash, n_bidders)
        self.n_rounds = 1
        self.others_cash = [cash for _ in range(self.n_bidders-1)]
        self.others_bids: list[list[int]] = [[] for _ in range(self.n_bidders-1)]
        
    def place_bid(self) -> int:
        # special cases
        if self.cash == 0:
            # no cash, no bid
            return 0
        if not any(self.others_cash):
            # no other players have cash, bid low
            return 1
        
        # bid 1 for the first n rounds
        # with n equivalent to the relevant bids option
        if self.n_rounds <= self.relevant_bids:
            return 1
        
        # calculate the sum of last bids of other players
        others_sum: list[int] = list(map(lambda bids: sum(bids[-self.relevant_bids:]),
                                         self.others_bids))
        
        # check if all other players are cooperating by bidding low
        if all(map(lambda x: x < self.max_amount, others_sum)):
            return 1
        else:
            bid_price = ceil(self.cash / self.quantity) + self.lead
            if bid_price <= self.cash:
                return bid_price
            else:
                return self.cash
    
    def notify_bids(self, others: list[int], sold: int) -> None:
        
        # record other's bidding activities
        others_bids: iter = iter(self.others_bids)
        others_cash: iter = iter(self.others_cash)
        
        for other in others:
            next(others_bids).append(other)
            next(others_cash).__sub__(other)
        
        # decrement the total quantity of this game
        self.quantity -= sold
        
        # increment the number of rounds
        self.n_rounds += 1
