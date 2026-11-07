"""Consumable items and effects for the Pac-Man game."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Sequence
from .logs import log, LogType

if TYPE_CHECKING:
    from .engine import GameEngine
    from .entities import Entity


class Effect(ABC):
    """Abstract base class for effects triggered by consumables."""

    @abstractmethod
    def apply(self, engine: GameEngine) -> None:
        """Apply the effect to the game engine.

        Args:
            engine: The game engine instance.
        """
        pass


class ScoreEffect(Effect):
    """Effect that awards points to the player score."""

    def __init__(self, score: int) -> None:
        """Initialize the score effect.

        Args:
            score: Number of points to add.
        """
        self._score: int = score

    def apply(self, engine: GameEngine) -> None:
        """Add points to the engine score.

        Args:
            engine: The game engine instance.
        """
        engine.add_score(self._score)


class FrightenGhostsEffect(Effect):
    """Effect that triggers frightened mode across all ghosts."""

    def __init__(self, duration: float) -> None:
        """Initialize the frightened effect.

        Args:
            duration: Duration in seconds for frightened mode.
        """
        self._duration: float = duration

    def apply(self, engine: GameEngine) -> None:
        """Trigger frightened mode in the game engine.

        Args:
            engine: The game engine instance.
        """
        engine.trigger_frightened_mode(self._duration)


class SpeedDebuffEffect(Effect):
    """Effect that reduces movement speed of target entities."""

    def __init__(
        self, duration: float, targets: Entity | Sequence[Entity]
    ) -> None:
        """Initialize the speed debuff effect.

        Args:
            duration: Duration in seconds for the debuff.
            targets: Target entity or sequence of entities.
        """
        self._duration: float = duration
        self._targets: Entity | Sequence[Entity] = targets

    def apply(self, engine: GameEngine) -> None:
        """Apply speed reduction to target entities.

        Args:
            engine: The game engine instance.
        """
        engine.decrease_speed(self._duration, self._targets)


class SpeedBuffEffect(Effect):
    """Effect that increases movement speed of target entities."""

    def __init__(
        self, duration: float, targets: Entity | Sequence[Entity]
    ) -> None:
        """Initialize the speed buff effect.

        Args:
            duration: Duration in seconds for the buff.
            targets: Target entity or sequence of entities.
        """
        self._duration: float = duration
        self._targets: Entity | Sequence[Entity] = targets

    def apply(self, engine: GameEngine) -> None:
        """Apply speed increase to target entities.

        Args:
            engine: The game engine instance.
        """
        engine.increase_speed(self._duration, self._targets)


class Consumable(ABC):
    """Abstract base class representing an edible item on the maze grid."""

    _counter: int = 0

    def __init__(self, effects: Sequence[Effect]) -> None:
        """Initialize the consumable and register it in the counter.

        Args:
            effects: Sequence of effects triggered upon consumption.
        """
        self._effects: Sequence[Effect] = effects
        Consumable._counter += 1

    @classmethod
    def still_any_consumables(cls) -> bool:
        """Check whether any consumables remain on the grid.

        Returns:
            bool: True if one or more consumables remain, False otherwise.
        """
        return cls._counter > 0

    @classmethod
    def decrease_counter(cls) -> None:
        """Decrement the global remaining consumable count."""
        cls._counter -= 1

    @classmethod
    def reset_counter(cls) -> None:
        """Reset the global consumable counter to zero."""
        cls._counter = 0

    @classmethod
    def pellets(cls) -> int:
        """Return the current count of remaining consumables.

        Returns:
            int: Remaining number of consumables.
        """
        return cls._counter

    def effect(self, engine: GameEngine) -> None:
        """Consume this item, decrement counter, and apply all its effects.

        Args:
            engine: The game engine instance.
        """
        if Consumable.still_any_consumables():
            Consumable.decrease_counter()

        for effect in self._effects:
            effect.apply(engine)


class PacGum(Consumable):
    """Standard collectible pellet awarding score."""

    pass


class SuperPacGum(Consumable):
    """Energizer pellet awarding score and triggering ghost vulnerability."""

    def effect(self, engine: GameEngine) -> None:
        """Consume energizer, log event, and trigger effects.

        Args:
            engine: The game engine instance.
        """
        log(
            "Super Pac-Gum consumed! Ghosts are now frightened.",
            "Consumable",
            LogType.INFO,
        )
        super().effect(engine)
