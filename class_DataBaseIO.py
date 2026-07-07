# Python libs
from pathlib import Path


# Project files
from class_Word import Word


class DataBaseIO:
    '''
    Функционал для работы с файлом базы слов:
    - чтение из файла (file_reader)
    - десериализация данных (header_parser, line_parser)
    - сериализация данных (header_compositor, line_compositor)
    - запись в файл (file_writer)

    Так же есть метод класса для создания новой пустой базы
    create_new_empty_db
    '''

    @classmethod
    def create_new_empty_db(cls,
        file_path: Path,
        name: str|None = None,
        description: str|None = None,
        tags: list[str]|tuple[str, ...]|None = None
    ):
        '''
        Создаёт новую пустую базу и сохраняет по указанному пути
        (см. header_compositor)
        '''
        try:
            if file_path.exists():
                if file_path.is_dir():
                    raise Exception('Указанный путь занят директорией')
                else:
                    raise Exception('Указанный путь уже занят другим файлом')
            else:
                header = cls.header_compositor(
                    name,
                    description if description else '',
                    [*tags] if tags else None
                )
                file_path.write_text(header, encoding='utf-8')
        except Exception as error:
            raise Exception(error, 'Проблема при создании пустой базы')

    @classmethod
    def file_reader(cls, file_path: Path, words: list) \
        -> tuple[str|list[str], ...]:
        '''
        Возвращает заголовок базы и заполняет полученный список словами
        '''
        try:
            with file_path.open('r', encoding='utf-8') as f:
                # Читаем заголовок
                header = cls.header_parser(f.readline())
                if not header:
                    raise Exception('Некорректный заголовок базы')

                for line in f.readlines():
                    if line != '' and line != '\n':
                        word, variants, stress, info = cls.line_parser(line)
                        words.append(Word(word, variants, stress, info))
                    else:
                        raise Exception('Некорректная запись слов в базе')
        except Exception as error:
            raise Exception(error,'Проблема при чтении файла базы')
        else:
            return header

    @staticmethod
    def file_writer(file_path: Path, data: str):
        '''Базовая логика записи в файл'''
        def get_last_char(i: int=1) -> str:
            '''Пытается получить последний символ в существующем файле'''
            f.seek(f.tell()-i)
            try:
                char = f.read(i)
            except UnicodeDecodeError:
                char = get_last_char(i=i+1)
            else:
                return char

        try:
            if '@@@abooktools database@@@' in data:
                with file_path.open('w', encoding='utf-8') as f:
                    f.write(data)
            else:
                with file_path.open('a+', encoding='utf-8') as f:
                    if f.tell() != 0:
                        if get_last_char() != '\n':
                            f.write('\n')
                    f.write(data)
        except Exception as error:
            raise Exception(error, 'Проблема записи в файл')

    @staticmethod
    def header_parser(line: str) -> tuple[str|list[str], ...] | None:
        '''
        Пытается прочитать заголовок из файла базы
        (см. также header_parser)

        Возвращает кортеж элементов:
            name: str - имя базы (может быть пустым)
            info: str - описание базы (может быть пустым)
            tags: list[str] - список с тэгами (может быть пустым)

        Если заголовок некорректный возвращает: None

        Корректные заголовки:
        @@@abooktools database@@@
        @@@abooktools database@@@<имя>@@@<описание>@@@<тэг>&&&<тэг>
        @@@abooktools database@@@<имя>@@@<описание>
        @@@abooktools database@@@<имя>
        @@@abooktools database@@@@@@<описание>
        @@@abooktools database@@@@@@<описание>@@@<тэг>&&&<тэг>
        @@@abooktools database@@@<имя>@@@@@@<тэг>&&&<тэг>
        @@@abooktools database@@@@@@@@@<тэг>
        '''
        elements = line.strip('\n').split('@@@')
        if 3 <= len(elements) <= 5:
            if elements[0] == '' and elements[1] == 'abooktools database':
                name = elements[2]
                description = \
                    elements[3] if len(elements) >= 4 else ''
                if len(elements) == 5:
                    tags = elements[4].split('&&&')
                else:
                    tags = []
                return name, description, tags
        else:
            return None

        def line_parser(line: str) -> tuple[str,list[str],list[str],list[str]]:
            '''
            Разбивает строку на составляющие:
            (cм. также line_compositor)
            - слово
            - варианты написания слова
            - конфигурации ударений
            - свободная информация (тэги, комментарии, уточнения, пример текста)

            Разделители: : , = - , @@@ &&&

            Общий вид строки:
            <слово>:<вариант>,<вариант>=<У>,<ГУ>-<ВУ>@@@<информация>&&&<инфо>
            У - номер буквы, на которую падает ударение
            *нумерация с 1 через все согласные и гласные буквы слова
            для сложных слов:
            ГУ - номер буквы, на которую падает главное ударение
            ВУ - номер буквы, на которую падает второе (дополнительное) ударение
            
            Конкертные примеры строк:
            остроконечный=9-1
            общепринятый=7-1@@@Источник: Штудинер
            ёжик:ежик,ёжег=1@@@существительное&&&и заблудился ёжик в тумане
            замок=2,4@@@несколько значений&&&зАмок как крепость&&&дверной замОк
            банан
            зоопарк@@@А не сходить ли нам в зоопарк?
            ёлочка:елочка@@@...в лесу родилась ёлочка...
            '''
            try:
                w_v_s_i = line.strip('\n').split('@@@')
                if len(w_v_s_i)==2 and w_v_s_i[1]:
                    info: list[str] = w_v_s_i[1].split('&&&')
                else:
                    info = []

                w_v_s = w_v_s_i[0].split('=')
                if len(w_v_s)==2 and w_v_s[1]:
                    stress: list[str] = w_v_s[1].split(',')
                else:
                    stress = []

                w_v = w_v_s[0].split(':')
                if len(w_v)==2 and w_v[1]:
                    variants: list[str] = w_v[1].split(',')
                else:
                    variants = []
                
                word = w_v[0]
                
                return word, variants, stress, info

            except Exception as error:
                raise Exception(error, 'Ошибка парсинга строки!')

        try:
            with file_path.open('r', encoding='utf-8') as f:
                # Читаем заголовок
                header = header_parser(f.readline())
                if header:
                    self.__name, self.__description, self.__tags = header
                else:
                    raise Exception('Некорректный заголовок базы')

                # Читаем слова
                self.__words = {}
                for line in f.readlines():
                    if line != '' and line != '\n':
                        word, variants, stress, info = line_parser(line)
                        self.__words.append(Word(word,variants,stress,[],info))
                    else:
                        raise Exception('Некорректная запись слов в базе')

        except Exception as error:
            raise Exception(error,'Проблема при чтении файла базы')
        else:
            self.__path = file_path
            self.__is_db_saved = True
            print(f'Файл загружен: {self.__path}')
            print(f'Имя базы: {self.__name}')
            print(f'Описание: {self.__info}')
            print(f'Слов в базе: {len(self.__words)}')

    @staticmethod
    def header_compositor(name: str, description: str, tags: list[str]) -> str:
        '''
        Создаёт обязательный заголовок для файла базы
        (см. также header_parser)

        @@@abooktools database@@@<имя базы>@@@<описание>@@@<тэг>&&&<тэг>

        Имя базы может быть пустым, описание может быть пустым,
        тэгов может не быть
        Минимальный заголовок без имени и описания:
        @@@abooktools database@@@

        Примеры заголовков:
        @@@abooktools database@@@Моя база
        @@@abooktools database@@@Есть имя@@@Есть описани
        @@@abooktools database@@@@@@Нет имени, есть описание
        @@@abooktools database@@@База с тэгами@@@@@@названия&&&иностранные
        @@@abooktools database@@@@@@@@@только&&&тэги
        @@@abooktools database@@@@@@Есть описание и тэги@@@без имени
        '''
        header = '@@@abooktools database@@@'
        if name:
            if name.replace('@@@', '').replace('\n', ''):
                header += name
        if description:
            if description.replace('@@@', '').replace('\n', ''):
                header += f'@@@{description}'
        if tags:
            header += '@@@' if header.count('@') == 9 else '@@@@@@'
            for tag in tags:
                clean_tag = tag\
                    .replace('@@@', '')\
                    .replace('&&&', '')\
                    .replace('\n', '')
                header += f'{clean_tag}&&&'
        header = header.rstrip('&&&')
        header += '\n'
        return header

    @staticmethod
    def line_parser(line: str) \
    -> tuple[str, list[str], list[tuple[int,...]], list[str]]:
        '''
        Разбивает строку на составляющие:
        (cм. также line_compositor)
        - слово
        - варианты написания слова
        - конфигурации ударений
        - свободная информация (комментарии, уточнения, пример текста)

        Разделители: : , = - , @@@ &&&

        Общий вид строки:
        <слово>:<вариант>,<вариант>=<У>,<ГУ>-<ВУ>@@@<информация>&&&<информация>
        У - номер буквы, на которую падает ударение
        *нумерация с 1 через все согласные и гласные буквы слова
        для сложных слов:
        ГУ - номер буквы, на которую падает главное ударение
        ВУ - номер буквы, на которую падает второе (дополнительное) ударение
        
        Конкертные примеры строк:
        остроконечный=9-1
        общепринятый=7-1@@@Источник: Штудинер
        ёжик:ежик,ёжег=1@@@существительное&&&...и заблудился ёжик в тумане...
        замок=2,4@@@больше одного значения&&&зАмок как крепость&&&дверной замОк
        банан
        зоопарк@@@А не сходить ли нам в зоопарк?
        ёлочка:елочка@@@...в лесу родилась ёлочка...
        '''
        def stress_converter_from_str(stress: list[str]) \
        -> list[tuple[int,...]]:
            '''
            Превращает список со строками в список с кортежами из чисел:
            ['2','1','4-1','5-2-3'] -> [(2,), (1,), (4,1), (5,2,3)]
            '''
            converted_stress = []
            for s in stress:
                new_s = tuple(s.split('-'))
                converted_stress.append(new_s)
            return converted_stress

        try:
            w_v_s_i = line.strip('\n').split('@@@')
            if len(w_v_s_i)==2 and w_v_s_i[1]:
                info: list[str] = w_v_s_i[1].split('&&&')
            else:
                info = []

            w_v_s = w_v_s_i[0].split('=')
            if len(w_v_s)==2 and w_v_s[1]:
                stress: list[str] = w_v_s[1].split(',')
            else:
                stress = []

            w_v = w_v_s[0].split(':')
            if len(w_v)==2 and w_v[1]:
                variants: list[str] = w_v[1].split(',')
            else:
                variants = []
            
            word = w_v[0]
            stress = stress_converter_from_str(stress)
            
            return word, variants, stress, info

        except Exception as error:
            raise Exception(error, 'Ошибка парсинга строки!')

    @staticmethod
    def line_compositor(
        word: str,
        variants: list[str],
        stress: list[tuple[int,...]],
        info: list[str]
    ) -> str:
        '''
        Собирает строку из составляющих блоков для записи в файл:
        (cм. также line_parser)
        - само слово
        - варианты альтернативного написания слова
        - конфигурации ударений
        - блоки произвольной информации
            (комментарии, уточнения, пример текста)

        Декораторы и разделители:
        перед словом дополнительные символы не используются
        : используется перед вариантами
        , разделитель вариантов
        = используется перед конфигурациями ударений
        , разделитель конфигураций ударений
        @@@ используется перед блоками информации
        &&& разделитель блоков информации
        '''
        def block_compositor(elements:list,decorator:str,separator:str) -> str:
            block = ''
            end = -len(separator)
            for element in elements:
                # Очищаем элемент от запрещённых в блоке символов
                element = element\
                    .replace(decorator, '')\
                    .replace(separator, '')\
                    .replace('\n', '')
                if element:
                    block += f'{element}{separator}'
            if block:
                block = f'{decorator}{block[:end]}'
            return block

        def stress_converter_to_str(stress: list[tuple[int,...]]) -> list[str]:
            '''
            Превращает список со кортежами из чисел в список со строками:
            [(2,), (1,), (4,1), (5,2,3)] -> ['2','1','4-1','5-2-3']
            '''
            converted_stress = []
            for s in stress:
                string = ''
                for number in s:
                    string += f'{number}-'
                string = string.rstrip('-')
                converted_stress.append(string)
            return converted_stress

        # Собираем варианты слов:
        variants = block_compositor(variants, ':', ',')
        # Собираем конфигурации ударений
        stress = block_compositor(stress_converter_to_str(stress), '=', ',')
        # Собираем блоки информации
        info = block_compositor(info, '@@@', '&&&')

        line = word + variants + stress + info + '\n'
        return line