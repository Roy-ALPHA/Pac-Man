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
        self.duration = duration

    def apply(self, engine):
        engine.trigger_frightened_mode(self._duration)
