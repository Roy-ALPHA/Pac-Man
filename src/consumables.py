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

    def __init__(self, effects):
        self._effects = effects

    def effect(self, engine):
        for effect in self._effects:
            effect.apply(engine)


class PacGum(Consumable):
    pass


class SuperPacGum(Consumable):
    pass
