from abc import ABC, abstractmethod


class Effect(ABC):

    @abstractmethod
    def apply(self, engine):
        pass


class ScoreEffect(Effect):
    def __init__(self, score):
        self._score = score

    def apply(self, engine):
        engine.add_score(self._score)


class FrightenGhostsEffect(Effect):
    def __init__(self, duration):
        self._duration = duration

    def apply(self, engine):
        engine.trigger_frightened_mode(self._duration)


class Consumable(ABC):

    _counter = 0

    def __init__(self, effects):
        self._effects = effects
        Consumable._counter += 1

    @classmethod
    def still_any_consumables(cls):
        return cls._counter > 0

    @classmethod
    def reset_counter(cls):
        cls._counter = 0

    def effect(self, engine):
        if Consumable.still_any_consumables() > 0:
            Consumable._counter -= 1

        for effect in self._effects:
            effect.apply(engine)


class PacGum(Consumable):
    pass


class SuperPacGum(Consumable):
    pass
