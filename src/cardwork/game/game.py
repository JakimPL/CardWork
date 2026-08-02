from abc import ABC, abstractmethod

from cardwork.board.board import Board
from cardwork.cards.deck import Deck
from cardwork.game.state import GameState


class Game(ABC):
    players: int
    board: Board
    state: GameState

    def __init__(self, players: int, deck: Deck) -> None:
        self.validate_players(players)
        self.validate_initial_deck(deck)
        self.board = self.initialize(players, deck)

    @abstractmethod
    def initialize(self, players: int, deck: Deck) -> Board:
        """
        Set the initial board.
        """

    @abstractmethod
    def validate_players(self, players: int) -> None:
        """
        Conditions on the number of players.
        """

    @abstractmethod
    def validate_initial_deck(self, deck: Deck) -> None:
        """
        Additional checks for supported initial decks.
        """
