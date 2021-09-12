Auction bot
===

This auction bot competed in [the USRC x SYNCS Competitive Coding Challenge 2021](http://auctions11.usydrobotics.club/).

## Files

### Game files

Provided by the organiser, changes made for testing purpose

- `run_game.py`: 
  entrance to run game
- `gameEngine.py`:
  contains the game engine and NPC bot
- `template.py`:
  a coding template for competitor
- `exmaples` directory:
  some sample scripts

### Solution files

The `christie` directory contains our working solutions in different stages. They are developed in the following orders:

- `prob_guess.py`:
  using probability to guess NPC bots and report
- `hypo_testing.py`:
  using hypothesis testing to more accurately guess NPC bots
- `hypo_testing2.py`:
  updated hypothesis testing to be more accurate and improved bidding algorithm
- `cooperate.py`:
  share true value between team bots
- `cooperate_new.py`:
  slight improvement all aspects to adapt to the game
- `fresh_start.py`:
  completely reworked final solution

The `log_analyser.ipynb` file crawls the log files on game server. We use the logs to test different solutions and 
quantify their performance.  

## Solution

This section gives some explanation to our final solution in `fresh_start.py`.
The main features of our solution are:

- Communication protocol
- Hypothesis testing NPC bots
- Control flow

Our bot bids according to the following stages:

1. Team bot verification
2. Ture value sharing
3. Imitate NPC bots
4. Must bid if losing

### Communication protocol

In order to avoid being detected, our bots should also bid below the NPC bid increase in phase 1 and smaller than one 
standard deviation in phase 2. So we bid according to base n with n being 15 and 63 in phase 1 and 2 respectively.

#### Teammate (stage 1)

As long as the bots have not recognised their teammates, they bid the multiples of n-2, which happens to be a prime 
number. There could be other bots that accidentally bid in this pattern, but statistically the chance should be really 
small after just 2 rounds.

#### True value (stage 2)

Sharing true value using bids is a primary feature of all game bots. The game engine generates true value from a normal 
distribution truncated to one standard deviation left and right, so the protocol only needs to account for the amount 
of numbers that equal two times the standard deviation. Moreover, being a normal distribution, the true value is more 
likely to fall closely to the mean, so preferably numbers closer to the mean should be represented by a shorter 
sequence. With all these in mind, we developed a communication protocol that works as 
follows:

Given the true value (tv) of an auction, the mean (µ) and the standard deviation (σ) of true value distribution in a 
game, we first acquire the signed distance of true value from mean which is tv - µ. Then, we convert it to an unsigned 
number by multiplying its magnitude by 2, then add 1 if it's a negative number. This way, tv closer to mean would have 
a smaller absolute value, thus a smaller unsigned value. Then we convert it to base n. We should have obtained a 
sequence by now. In order to determine when a sequence is finished, the number n is padded if the sequence is shorter 
than the maximum possible sequence in a game. The maximum length is ceiling(log(2σ) / log(n)).

### Hypothesis testing NPC bots

Enemy recognition and reporting is another big part of this competition. For that we need to exclude team bots, but 
also NPC bots. The code of NPC bots is given in `gameEngine.py`. The probability of it bidding is per stage (npc_p): 

- low stage (last bid < µ/4) : 0.64
- mid stage (µ/4 < last bid < 3µ/4) : 0.32
- high stage (last bid > 3µ/4) : 0.04

We record the times that a bot bid and the chance it is given to bid in all stages. Then we can calculate the 
percentage of it bidding when given the chance (p). We hypothesise that the bot is NPC bot so that it's bidding 
probability is p = npc_p. Using the normal distribution with npc_p as mean and npc_p(1-npc_p)/√n as standard deviation, 
we obtain the test statistic (i.e. z-score) for the bot being NPC at each stage. In phase 2, we perform adidtional 
testing for the bid increase. We then combine the test statistics using weighted z-method ([reference](https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.1420-9101.2005.00917.x)).
At last, we obtain the final p-value for that bot being the NPC bot. If it is below a certain threshold, we reject the 
null hypothesis and consider it an enemy bot. The optimum threshold is determined using the code `log_analyer.ipynb`.

## Author

Edward Ji, Jenny Lin, Kevin Min 2021