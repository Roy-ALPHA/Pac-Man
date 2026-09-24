from abc import ABC, abstractmethod


class Consumable(ABC):

    def __init__(self, effects):
        self._effects = effects

    @abstractmethod
    def consume(self, engine):
        pass


class PacGum(Consumable):
    def __init__(self, effects):
        super().__init__(effects)

    def consume(self, engine):
        for effect in self._effects:
            effect.apply(engine)


class SuperPacGum(Consumable):
    def __init__(self, effects):
        super().__init__(effects)

    def consume(self, engine):
        for effect in self._effects:
            effect.apply(engine)
