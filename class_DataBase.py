# Python libs
from pathlib import Path


# Project files
from class_Word import Word
from class_DataBaseIO import DataBaseIO


class DataBase:
    def __init__(self):
        # Сохранены ли изменения самой базы в файл (если были)?
        # (Не учитывает список новых слов, предлагаемых к записи в базу)
        self.__is_db_saved: bool = False
        # Используется ли база при сканировании текста
        self.__in_use: bool = False
        # Путь к файлу базы
        self.__path: Path|None = None
        # Название базы
        self.__name: str = ''
        # Описание базы
        self.__description: str = ''
        # Особые метки
        self.__tags: list[str] = []
        # Загруженные слова из файла базы
        self.__words: list[Word] = []
        # Новые слова для сохранения в файл базы
        self.__buffer: list[Word] = []
        self.__IO = DataBaseIO

    @property
    def path(self) -> Path:
        return self.__path
    @property
    def name(self) -> str:
        return self.__name
    @property
    def description(self) -> str:
        return self.__description
    @property
    def tags(self) -> tuple[str, ...]:
        return tuple(self.__tags)
    @property
    def words(self) -> iterator:
        return iter(self.__words)
    @property
    def word_count(self) -> int:
        return len(self.__words)
    @property
    def buffer_word_count(self) -> int:
        return len(self.__buffer)

    @property
    def buffer(self) -> list[Word]:
        return self.__buffer

    def in_use(self, set_flag: None|bool = None) -> bool:
        '''
        Вызов без параметров возвращает состояние базы
        (заглядывать ли в базу при отборе новых слов)
        При передаче True или False устанавливает состояние
        '''
        if set_flag != None:
            self.__in_use = set_flag
        return self.__in_use

    def change_info(self,
        name: str = None,
        description: str = None,
        tags_to_add: str|tuple[str, ...]|list[str] = None,
        tags_to_del: str|tuple[str, ...]|list[str] = None
    ):
        if name or description or tags_to_add or tags_to_del:
            self.__is_db_saved = False
        if name:
            self.__name = name
        if description:
            self.__description = description
        if tags_to_add:
            if type(tags_to_add) == str:
                self.__tags.append(tags_to_add)
            if type(tags_to_add) == tuple or type(tags_to_add) == list:
                self.__tags.extend(tags_to_add)
        if tags_to_del:
            if type(tags_to_del) == str:
                self.__tags.remove(tags_to_del)
            if type(tags_to_del) == tuple or type(tags_to_del) == list:
                for tag in tags_to_del:
                    self.__tags.remove(tag)

    def load(self, file_path: Path):
        '''
        Загружает базу из указанного файла
        '''
        self.__words.clear()
        self.__name, self.__description, self.__tags = \
            self.__IO.file_reader(file_path, self.__words)
        self.__is_db_saved = True
        self.__path = file_path

    def save(self,
        file_path: Path = None,
        save_without_new_words: bool = False,
        sort_db_words: bool = False
    ):
        '''
        Сохраняет базу.
        Если были назначены новые слова к добавлению, но сама база
        не редактировалась, то просто дописывает слова в конец файла
        Если редактировалась база, то сохраняет в файл изменения и новые слова,
        при этом слова будут отсортированы по алфавиту
        (потребуется полная перезапись файла)

        file_path: Path
        Если явно передан путь к файлу, сохранит копию базы в этот новый файл,
        при этом указанный путь должен быть свободен, а текущий экземпляр базы
        останется не сохранённым
        (так же учитывается параметр save_without_new_words:)

        save_without_new_words: bool
        True - сохранит только данные самой базы из памяти в файл,
               не включая новые добавленные во время сессии слова
        False - стандартное сохранение базы с записью новых слова

        sort_db_words: bool
        True - при сохранении базы принудительно отсортирует слова по алфавиту
        False - решение о сортировке примется автоматически
        '''

        def alphabet_sort(word: Word) -> tuple:
            spec_chars = "-'`_"
            rus_chars = 'АаБбВвГгДдЕеЁёЖжЗзИиЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя'
            eng_chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz'
            digit_chars = '1234567890'
            allowed_chars = spec_chars + rus_chars + eng_chars + digit_chars
            chars_order = {char: idx for idx, char in enumerate(allowed_chars)}
            return tuple(chars_order.get(char) for char in word)

        if file_path == None:
            file_path = self.__path
        words: list = []
        data: str = ''

        # "Сохранить как" режим. Изменения записываются в другой файл
        if file_path != self.__path:
            if file_path.exists():
                raise Exception(
                    'Указанный путь уже занят другим файлом или директорией'
                )
            else:
                # Готовим для записи заголовок
                data += self.__IO.header_compositor(
                    self.__name,
                    self.__description,
                    self.__tags
                )
                # Готовим для записи слова имеющиеся в базе
                words.extend(self.__words)
                # Если не запрещено, готовим к записи новые слова из буфера
                if not save_without_new_words:
                    words.extend(self.__buffer)
                # Сортируем последовательность всех слов по алфавиту
                words.sort(key=alphabet_sort)

        # "Сохранить" режим. Ниже варианты обычного сохранения в тот же файл
        # Если сама база не была изменена
        elif self.__is_db_saved:
            # Если не запрещено, готовим к записи новые слова из буфера
            if not save_without_new_words:
                words.extend(self.__buffer)
            # Если стоит флаг принудительной сортировки
            if sort_db_words:
                # Понадобится пересоздать заголовок
                data += self.__IO.header_compositor(
                    self.__name,
                    self.__description,
                    self.__tags
                )
                # Существующие слова тоже готовим к записи
                words.extend(self.__words)
                # Сортируем все слова старые + новые (если есть и разрешено)
                words.sort(key=alphabet_sort)
        # Если выполнялось редактирование самой базы
        else:
            # Готовим заголовок
            data += self.__IO.header_compositor(
                self.__name,
                self.__description,
                self.__tags
            )
            # Готовим существующие слова
            words.extend(self.__words)
            # Готовим также новые слова, если не запрещено
            if not save_without_new_words:
                words.extend(self.__buffer)
            # Сортируем все слова
            words.sort(key=alphabet_sort)

        # Формируем из подготовленных слов массив текста
        for word in words:
            data += self.__IO.line_compositor(
                word,
                word.variants,
                word.stress,
                word.info
            )
        # Текст для записи полностью сформирован
        data = data.rstrip('\n')

        # Проверяем: в итоге есть ли данные, которые нужно записать?
        # (чтобы не открывать файл для записи пустоты)
        if data:
            # Записываем подготовленные данные в файл
            self.__IO.file_writer(file_path, data)
            # Если сохранение было в тот же файл, помечаем, что база сохранена
            if file_path == self.__path:
                self.__is_db_saved = True
                # Если было не запрещено записывать новые слова,
                # очищаем буфер, т.к. слова уже записаны
                if not save_without_new_words:
                    self.__words.extend(self.__buffer)
                    self.__buffer.clear()