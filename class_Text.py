# Python libs
from pathlib import Path


# Project files
from class_Word import Word


class Text:
    '''
    Класс для загрузки текста из файла и разложения его на слова.
    Работает только с простыми текстовыми файлами в кодировке utf-8

    Формирует коллекции неповторяющихся слов и всех их позиций в тексте:
    отдельная коллекция для обычных слов и отдельная для имён/названий
    '''
    def __init__(self):
        # Весь текст файла в виде строки
        self.__text: str = ''
        # Длина всего текста как строки (в символах)
        self.__text_length: int = 0
        # Всего слов в тексте (включая повторы слов)
        self.__all_words_count: int = 0
        # Уникальные слова со всеми их позициями (кроме возможных имён)
        self.__unique_words: list[Word] = []
        # Возможные имена/названия и их позиции
        self.__unique_names: list[Word] = []

    def load(self, file_path: Path):
        '''
        Принимает путь к файлу. Загружает текст из файла.
        Работает только с простыми текстовыми файлами в кодировке utf-8
        '''
        self.drop() # очищаем текущее состояние
        try:
            # Загружаем весь текст в переменную в виде строки
            with file_path.open('r', encoding='utf-8') as f:
                self.__text = f.read()
        except Exception as error:
            raise Exception(error, 'Проблема при чтении файла')
        else:
            print(f'Загружен текст из файла: {file_path}')
            self.scan()

    def scan(self):
        '''
        Парсинг из текста слов и всех их встречаемых позиций.
        Делает две коллекции: для имён/названий и для обычных слов.
        Каждое слово/имя в список заносится один раз, но для него указываются
        все позиции (индекс символа текста), где оно встречалось.
        '''
        # Получаем кличество символов в тексте
        self.__text_length: int = len(self.__text)

        # Группы символов, которые могут встречаться в словах
        chars_lat: str = "qwertyuiopasdfghjklzxcvbnm"
        chars_LAT: str = "QWERTYUIOPASDFGHJKLZXCVBNM"
        chars_cyr: str = "йцукенгшщзхъёфывапролджэячсмитьбю"
        chars_CYR: str = "ЙЦУКЕНГШЩЗХЪЁФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"
        chars_spec: str = "-'`_1234567890"
        # Все символы, которые могут встречаться в словах
        allowed_chars: str = \
            chars_cyr + chars_CYR + chars_spec + chars_lat + chars_LAT
 
        # список со всеми словами текста и их позициями
        all_words : list[tuple[str, [int]]] = []
        word : str = '' # текущее слово в процессе поисков
        word_pos : int = 0 # позиция текущего слова

        # Посимвольно читаем текст и ищем слова
        for pos, char in enumerate(self.__text):
            # Если допустимый символ, составляем из него текущее слово
            if char in allowed_chars:
                if word == '': # если символ первый в слове, запоминаем позицию
                    word_pos = pos
                    # Оставляем заглавные буквы в именах,
                    # переводим в строчные в обычных словах
                    if char.isupper():
                        if all_words:
                            pwe_pos = all_words[-1][1] + len(all_words[-1][0])
                            if (
                                ('.' in self.__text[pwe_pos:pos])
                                or ('!' in self.__text[pwe_pos:pos])
                                or ('?' in self.__text[pwe_pos:pos])
                                or ('\n' in self.__text[pwe_pos:pos])
                            ):
                                char = char.lower()
                        else:
                            char = char.lower()
                word += char
                # Чтобы не пропустить самое последнее слово:
                if pos+1 == self.__text_length:
                    if word[0].isupper():
                        all_words.append((word, word_pos))
                    else:
                        all_words.append((word.lower(), word_pos))
            # Если недопустимый символ, завершаем составление текущего слова
            # или ищем следующий допустимый символ
            else:
                if word:
                    # Исключаем ненастоящие слова
                    if (
                        (word == '-')
                        or (word == '_')
                        or (word == "'")
                        or (word == '`')
                    ):
                        word = ''
                    else:
                        if word[0].isupper():
                            all_words.append((word, word_pos))
                        else:
                            all_words.append((word.lower(), word_pos))
                        word = ''

        self.__all_words_count = len(all_words)
        self.__unique_words.clear()
        self.__unique_names.clear()

        # Ищем и оставляем только уникальные слова
        # сохраняем все позиции, на которых встречается слово в тексте
        while all_words:
            unique_word : str = all_words[0][0]
            unique_word_pos : list[int] = []
            pos_to_del : list[int ]= []
            for pos, word in enumerate(all_words):
                if unique_word == word[0]:
                    unique_word_pos.append(all_words[pos][1])
                    pos_to_del.append(pos)
            for pos in reversed(pos_to_del):
                all_words.pop(pos)
            # Обычные слова в один список, имена в другой
            if unique_word[0].isupper():
                self.__unique_names.append(
                    Word(unique_word, positions=unique_word_pos)
                )
            else:
                self.__unique_words.append(
                    Word(unique_word, positions=unique_word_pos)
                )

    def drop(self):
        self.__text = ''
        self.__text_length = 0
        self.__all_words_count = 0
        self.__unique_words.clear()
        self.__unique_names.clear()

    def fragment(self, start: int, end: int) -> str:
        return self.__text[start:end]

    def fragment_before(self,
        word_pos: int,
        word_len: int,
        size: int|tuple(int, int)
    ) -> str:
        fragment = ''
        start = word_pos - size if type(size) == int else word_pos - size[0]
        if start < 0:
            start = 0
        end = word_pos
        fragment = self.__text[start:end]
        return fragment

    def fragment_after(self,
        word_pos: int,
        word_len: int,
        size: int|tuple(int, int)
    ) -> str:
        fragment = ''
        start = word_pos + word_len
        end = word_pos + word_len
        end += size if type(size) == int else size[1]
        if end > self.__text_length:
            end = self.__text_length
        fragment = self.__text[start:end]
        return fragment

    @property
    def length(self) -> int:
        return self.__text_length
    @property
    def unique_words(self) -> list[Word]:
        return self.__unique_words
    @property
    def unique_names(self) -> list[Word]:
        return self.__unique_names
    @property
    def count_unique_words(self) -> int:
        return len(self.__unique_words)
    @property
    def count_unique_names(self) -> int:
        return len(self.__unique_names)
    @property
    def count_all_words(self) -> int:
        return self.__all_words_count