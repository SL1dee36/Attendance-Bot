import random

twentyone_rules = """
**21 (Blackjack) Rules:**

* **Goal:** Get as close to 21 as possible without going over.
* **Card Values:** 2-10 are face value, J, Q, K are 10, A is 1 or 11.
* **Gameplay:** Each player is dealt two cards. Players can choose to "hit" (take another card) or "stand" (keep their current hand).
* **Winning:** The player closest to 21 without busting wins.  If a player gets 21 exactly (Blackjack), they immediately win unless the dealer also has Blackjack. If a player busts (goes over 21), they lose.
* **Dealer Rules:**  The dealer must hit until their hand total is 17 or more.  The dealer wins ties.
"""


def create_deck():
    suits = ["♣", "♦", "♥", "♠"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    deck = [{"rank": rank, "suit": suit} for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def calculate_hand_value(hand):
    ace_count = hand.count('A')
    total = 0
    for card in hand:
        if card.isdigit():
            total += int(card)
        elif card in ('J', 'Q', 'K'):
            total += 10
        elif card == 'A':
            total += 11

    while total > 21 and ace_count > 0:
        total -= 10
        ace_count -= 1
    return total

def deal_card(deck):
    return deck.pop()

def format_hand(hand):
    return " ".join([f"{card['rank']}{card['suit']}" for card in hand])