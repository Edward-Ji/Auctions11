from abc import abstractmethod


class Bidder:
    """
    Represents a bidder for the auction
    """
    
    def __init__(self, number: int, **options):
        """
        Constructor a Bidder object with a unique name
        :param number: unique number id of this bidder
        """
        self.cash: int = 0
        self.quantity: int = 0
        self.n_bidders: int = 0
        self.acquired: float = 0
        self._name = "Bidder no.{}: {}".format(
            number,
            type(self).__name__.removesuffix("Bidder")
        )
        for key, value in options.items():
            setattr(self, key, value)
    
    @property
    def name(self):
        return self._name
    
    def start_game(self, quantity: int, cash: int, n_bidders: int):
        """
        Initialise values of an auction game
        :param quantity: the quantity
        :param cash: the starting cash
        :param n_bidders: the number of bidders
        """
        self.cash = cash
        self.quantity = quantity
        self.n_bidders = n_bidders
        self.acquired = 0

    @abstractmethod
    def place_bid(self) -> float:
        """
        Returns the bid for the current auctioning product (>= 0)
        :return: the next bid
        """
        pass
    
    @abstractmethod
    def notify_bids(self, others: list[float], sold: int) -> None:
        """
        Notify player of the bids of all other bidders
        :param others: a list of all bids by the other bidders
        :param sold: the quantity sold this round
        """
        pass
