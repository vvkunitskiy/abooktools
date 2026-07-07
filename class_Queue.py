# Python libs
from enum import Enum


# Project files
from class_Word import Word, WordStatus


class QueueView(Enum):
    PENDING = 0 # Ещё не обработанные слова
    HANDLED = 1 # Слова добавленные в какую-то базу
    IGNORED = 2 # Слова помеченные как игнорируемые
    ALL = 3 # Все слова


class QueueOrder(Enum):
    BY_ALPHABET = 'Сортировка по алфавиту'
    BY_ALPHABET_REVERSE = 'Сортировка по алфавиту в обратном порядке'
    BY_COUNT = 'Сортировка по встречаемости слова'
    BY_COUNT_REVERSE = 'Сортировка по встречаемости слова по убыванию'
    BY_LENGTH = 'Сортировка по длине слова'
    BY_LENGTH_REVERSE = 'Сортировка по длине слова по убыванию'
    BY_POSITION = 'Сортировка по первому включению слова с начала в конец'
    BY_POSITION_REVERSE = 'Сорт-ка по первому включению слова из конца в начало'


class Queue(list):
    '''
    Очередь со словами, требующими принятия решения:
    - пропустить (вернуться позже)
    - игнорировать (не возвращаться к слову)
    - добавить в одну из баз
    '''
    def __init__(self, *args: Word):
        super().__init__()
        self.__current_word: Word|None = None
        for arg in args:
            self.append(arg)

    def append(self, word: Word):
        '''
        Добавит в конец списка слово
        Переопределение append от list
        '''
        if isinstance(word, Word):
            super().append(word)
        if self.__current_word == None:
            self.__current_word = self[-1]

    def extend(self, iterable):
        super().extend(iterable)
        if self.__current_word == None:
            for w in self:
                if w.status == WordStatus.PENDING:
                    self.__current_word = w
                    break

    def clear(self):
        super().clear()
        self.__current_word = None
        self.__current_view = 3

    def goto_next(self):
        '''
        Сдвигает указатель позиции в очереди
        на следующее необработанное слово
        '''
        index = 0
        for i, w in enumerate(self):
            if w == self.__current_word:
                index = i
                break
        word = None
        for w in self[index+1 if index < len(self)-1 else 0:]:
            if w.status == WordStatus.PENDING:
                word = w
                break
        if word == None:
            for w in self[:index+1]:
                if w.status == WordStatus.PENDING:
                    word = w
                    break
        self.__current_word = word

    @property
    def current_word(self) -> Word|None:
        '''
        Возвращает текущее слово, требующее принятия решения.
        Если все слова в очереди обработаны, возвращает None
        '''
        return self.__current_word

    @property
    def pending(self) -> iterator[Word]:
        return (w for w in self if w.status == WordStatus.PENDING)

    @property
    def handled(self) -> iterator[Word]:
        return (w for w in self if w.status == WordStatus.HANDLED)

    @property
    def ignored(self) -> iterator[Word]:
        return (w for w in self if w.status == WordStatus.IGNORED)

    @property
    def count_pending(self) -> int:
        return len([w for w in self if w.status == WordStatus.PENDING])

    @property
    def count_handled(self) -> int:
        return len([w for w in self if w.status == WordStatus.HANDLED])

    @property
    def count_ignored(self) -> int:
        return len([w for w in self if w.status == WordStatus.IGNORED])

    @property
    def count(self) -> int:
        return len(self)

    def sort_by_alphabet(self, reverse: bool = False):
        '''
        Отсортировать очередь по алфавиту.
        С флагом reverse = True сортирует по альфавиту в обратном порядке.
        '''
        def alphabet_sort(w: Word) -> tuple:
            spec_chars = "-'`_"
            rus_chars = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
            eng_chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz'
            digit_chars = '1234567890'
            allowed_chars = spec_chars + rus_chars + eng_chars + digit_chars
            chars_order = {char: idx for idx, char in enumerate(allowed_chars)}
            return tuple(chars_order.get(char) for char in w)
        self.sort(reverse=reverse, key=alphabet_sort)

    def sort_by_length(self, reverse: bool = False):
        '''
        Отсортировать очередь по длине слова (сначала короткие).
        С флагом reverse = True сортирует в обратном порядке.
        '''
        self.sort(reverse=reverse, key=lambda w: len(w))

    def sort_by_count(self, reverse: bool = False):
        '''
        Отсортировать очередь по количеству повторений слова (сначала редкие).
        С флагом reverse = True сортирует в обратном порядке (сначала частые).
        '''
        self.sort(reverse=reverse, key=lambda w: len(w.positions))

    def sort_by_position(self, reverse: bool = False):
        '''
        Отсортировать очередь по первой встреченной позиции слова
        (с начала в конец)
        С флагом reverse = True сортирует в обратном порядке:
        первая встреченная позиция слова от конца в начало
        '''
        if reverse:
            self.sort(reverse=reverse, key=lambda w: w.positions[-1])
        else:
            self.sort(reverse=reverse, key=lambda w: w.positions[0])