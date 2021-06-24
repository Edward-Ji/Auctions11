from random import random

from bidder import Bidder


class RandomBidder(Bidder):
    
    def __init__(self, number: int, **options):
        """
        :param number:
        :param options:
            max_bid: the upper limit of random integer
        """
        # default values for options
        self.max_bid = 4
        super(RandomBidder, self).__init__(number, **options)
        
    def place_bid(self) -> float:
        return random() * min(self.max_bid, self.cash)

    def notify_bids(self, others: list[float], sold: int) -> None:
        pass
