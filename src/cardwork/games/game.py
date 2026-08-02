from abc import ABC, abstractmethod

from cardwork.boards.board import Board
from cardwork.decks.deck import Deck
from cardwork.decks.draw import shuffle_deck
from cardwork.games.state import GameState


class Game(ABC):
    players: int
    board: Board
    state: GameState

    def __init__(
        self,
        players: int,
        deck: Deck,
        *_args: object,
        shuffle: bool = True,
        **_kwargs: object,
    ) -> None:
        self._basic_initial_validation(players, deck)
        self._validate_players(players)
        self._validate_initial_deck(deck)
        deck = self._shuffle(deck, shuffle)
        self.board = self._deal_cards(players, deck)
        self.state = self._initialize(players, deck)
        self._basic_final_validation()
        self._final_validation()

    def _basic_initial_validation(self, players: int, deck: Deck) -> None:
        if players < 1:
            raise ValueError(f"Expected at least 1 player, got {players}")

        if not deck:
            raise ValueError("Deck cannot be empty")

    def _basic_final_validation(self) -> None:
        if self.state.points is None:
            return

        points_table_size = len(self.state.points)
        if self.players != points_table_size:
            raise ValueError(
                f"Points table size {points_table_size} does not match the number of players: {self.players}"
            )

        self.board.validate_board()

    def _shuffle(self, deck: Deck, shuffle: bool) -> Deck:
        if shuffle:
            return shuffle_deck(deck)

        return deck

    @abstractmethod
    def _deal_cards(self, players: int, deck: Deck) -> Board:
        """
        Deal cards to the player and the table.
        """

    @abstractmethod
    def _initialize(
        self,
        players: int,
        deck: Deck,
        *args: object,
        **kwargs: object,
    ) -> GameState:
        """
        Initialize the game.
        """

    @abstractmethod
    def _validate_players(self, players: int) -> None:
        """
        Conditions on the number of players.
        """

    @abstractmethod
    def _validate_initial_deck(self, deck: Deck) -> None:
        """
        Additional checks for supported initial decks.
        """

    @abstractmethod
    def _final_validation(self) -> None:
        """
        Final board and state validation
        """

    def _next_player(self) -> None:
        """
        Ends a turn of a player.
        """
        next_player = (self.state.player + 1) % self.players
        self.state.model_copy(update={"player": next_player})
