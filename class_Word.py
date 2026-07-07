# Python libs
from enum import Enum


class WordStatus(Enum):
    PENDING = 0 # Ещё не обработанные слова
    HANDLED = 1 # Слова добавленные в какую-то базу
    IGNORED = 2 # Слова помеченные как игнорируемые


class Word(str):
    def __new__(cls,
        word: str,
        variants: list[int] = [],
        stress: list[tuple[int, ...]] = [],
        info: list[str] = [],
        positions: list[int] = [],
    ):
        new_word = super().__new__(cls, word)
        return new_word

    def __init__(self,
        word: str,
        variants: list[int] = [],
        stress: list[tuple[int, ...]] = [],
        info: list[str] = [],
        positions: list[int] = [],
    ):
        # Варианты альтернативного написания слова
        self.__variants = variants.copy()
        # Конфигурации ударений
        self.__stress = stress.copy()
        # Позиции слова в тексте
        self.__positions = positions.copy()
        # Блоки произвольной информации о слове
        self.__info = info.copy()
        # Статус слова в очереди обработки
        self.__status: WordStatus = WordStatus.PENDING

        if 'ё' in word or 'Ё' in word:
            variant = word.replace('ё', 'е').replace('Ё','Е')
            self.__variants.append(variant)

    def __repr__(self):
        return f'{self}({self.variants}{self.stress}{self.info}{self.positions}{self.status.value})'

    @property
    def variants(self) -> list[str]:
        return self.__variants
    @property
    def stress(self) -> list[tuple]:
        return self.__stress
    @property
    def positions(self) -> list[int]:
        return self.__positions
    @property
    def info(self) -> list[str]:
        return self.__info
    @property
    def status(self) -> WordStatus:
        return self.__status
    @status.setter
    def status(self, status: WordStatus):
        if isinstance(status, WordStatus):
            self.__status = status