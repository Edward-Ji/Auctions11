import logging

from bidder import Bidder
from random_bidder import RandomBidder
from tit4tat_bidder import Tit4TatBidder

logging.basicConfig(filename='debug.log',
                    filemode='w',
                    level=logging.DEBUG)


class Auction:

    def __init__(self):
        self._n_rounds = 0
        self._start_cash: int = 100
        
        self.q_per_auction: int = 2

        self.bidders: list[Bidder] = [
            RandomBidder(1, max_bid=2),
            RandomBidder(2, max_bid=3),
            RandomBidder(3),
            RandomBidder(4, max_bid=5),
            RandomBidder(5, max_bid=6),
            Tit4TatBidder(6, lead=1),
            Tit4TatBidder(7),
            Tit4TatBidder(8, lead=3),
            Tit4TatBidder(9, lead=4),
            Tit4TatBidder(10, lead=5),
        ]
        
    @property
    def n_bidders(self) -> int:
        """The number of bidders this run"""
        return len(self.bidders)
        
    def game(self) -> list[Bidder]:
        quantity: int = 100
        
        for bidder in self.bidders:
            bidder.start_game(quantity, self._start_cash, self.n_bidders)
        
        while quantity > 0:
            logging.debug("quantity left: {}".format(quantity))
            # make bidders place bids
            bids: list[float] = []
            for bidder in self.bidders:
                bid: float = bidder.place_bid()
                logging.debug("{} places bid {}".format(bidder.name, bid))
                if bidder.cash < bid:
                    bid = 0
                bids.append(bid)
            
            # abort auction if all bidders are broke
            if all(map(lambda b: b.cash == 0, self.bidders)):
                break
            
            # distribute
            max_bid_val: float = 0
            max_bidders: list[Bidder] = []
            bids_iter = iter(bids)
            for bidder in self.bidders:
                bid = next(bids_iter)
                if bid > max_bid_val:
                    max_bid_val = bid
                    max_bidders = [bidder]
                elif bid == max_bid_val:
                    max_bidders.append(bidder)

            for bidder in max_bidders:
                bidder.cash -= max_bid_val / len(max_bidders)
                bidder.acquired += 1 / len(max_bidders)
                quantity -= 1
                logging.debug("{} acquired the item".format(
                    ", ".join(map(lambda b: b.name, max_bidders))
                ))

            # notify them of others bids
            i: int = 0
            for bidder in self.bidders:
                bidder.notify_bids(bids[:i] + bids[i + 1:], 1)
            
        # determine winner
        max_acq_val: float = 0
        max_bidders = []
        for bidder in self.bidders:
            if bidder.acquired > max_acq_val:
                max_acq_val = bidder.acquired
                max_bidders = [bidder]
            elif bidder.acquired == max_acq_val:
                max_bidders.append(bidder)
                
        return max_bidders


def test(n: int):
    auction = Auction()
    win_counts: dict[Bidder, int] = {}
    for _ in range(n):
        winners: list[Bidder] = auction.game()
        if len(winners) == 1:
            score: int = 3
        else:
            score: int = 1
        for winner in winners:
            if winner not in win_counts:
                win_counts[winner] = 0
            win_counts[winner] += score
    
    for player, n_win in sorted(win_counts.items(),
                                key=lambda bn: bn[1],
                                reverse=True):
        print("{:24} score {:5}".format(player.name, n_win))


test(1)
