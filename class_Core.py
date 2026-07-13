# Python libs
from itertools import chain
from pathlib import Path


# Project files
from class_DataBase import DataBase
from class_Text import Text
from class_Queue import Queue
from class_Config import Config
from class_Queue import QueueView, QueueOrder
from class_Word import Word, WordStatus
from messages import UiMsg, CoreMsg


class Core:
    def __init__(self):
        self.ui = None
        self.__config: Config = Config()
        self.__last_dir_for_text: str = None
        self.__last_dir_for_db: str = None
        self.__dbs: list[DataBase] = []
        self.__text: Text = Text()
        self.__words_queue: Queue = Queue()
        self.__names_queue: Queue = Queue()

        self.__fragment_size = 100
        self.__fragment_size_step = 5
        self.__current_queue: int = 0
        self.__words_queue_view = QueueView.ALL
        self.__names_queue_view = QueueView.ALL
        self.__current_word_position_index: int = 0
        self.__current_name_position_index: int = 0

    @property
    def current_word(self) -> Word:
        if self.__current_queue == 0:
            return self.__words_queue.current_word
        elif self.__current_queue == 1:
            return self.__names_queue.current_word

    @property
    def current_word_raw(self) -> str:
        return self.__text.fragment(
            self.current_word_position,
            self.current_word_position+len(self.current_word)
        )

    @property
    def current_word_position(self) -> int:
        if self.__current_queue == 0:
            return self.__words_queue.\
                current_word.positions[self.__current_word_position_index]
        elif self.__current_queue == 1:
            return self.__names_queue.\
                current_word.positions[self.__current_name_position_index]

    @property
    def current_word_position_index(self) -> int:
        if self.__current_queue == 0:
            return self.__current_word_position_index
        elif self.__current_queue == 1:
            return self.__current_name_position_index

    @property
    def text(self) -> Text:
        return self.__text

    def fragment_before(self,
        word_pos: int,
        word_len: int,
        size: int|tuple(int, int)
    ) -> str:
        return self.__text.fragment_before(word_pos, word_len, size)

    def fragment_after(self,
        word_pos: int,
        word_len: int,
        size: int|tuple(int, int)
    ) -> str:
        return self.__text.fragment_after(word_pos, word_len, size)

    @property
    def fragment_size(self) -> int:
        return self.__fragment_size

    @property
    def current_queue_view(self) -> Queue|iterator[Word]:
        if self.__current_queue == 0:
            match self.__words_queue_view:
                case QueueView.ALL:
                    return self.__words_queue
                case QueueView.PENDING:
                    return self.__words_queue.pending
                case QueueView.HANDLED:
                    return self.__words_queue.handled
                case QueueView.IGNORED:
                    return self.__words_queue.ignored
        elif self.__current_queue == 1:
            match self.__names_queue_view:
                case QueueView.ALL:
                    return self.__names_queue
                case QueueView.PENDING:
                    return self.__names_queue.pending
                case QueueView.HANDLED:
                    return self.__names_queue.handled
                case QueueView.IGNORED:
                    return self.__names_queue.ignored

    @property
    def current_queue(self) -> Queue:
        if self.__current_queue == 0:
            return self.__words_queue
        elif self.__current_queue == 1:
            return self.__names_queue

    @property
    def count_words(self) -> int:
        return self.__words_queue.count

    @property
    def count_names(self) -> int:
        return self.__names_queue.count

    def database(self, index: int) -> DataBase:
        return self.__dbs[index]

    @property
    def last_dir_for_db(self) -> str:
        return self.__last_dir_for_db

    @property
    def last_dir_for_text(self) -> str:
        return self.__last_dir_for_text

    def load_config(self):
        self.__config_load()

    def core_receiver(self, msg: UiMsg, extra = None):
        match msg:
            case UiMsg.TEST:
                print(UiMsg.TEST.value)

            case UiMsg.LOAD_TEXT:
                self.__text.load(extra)
                self.__last_dir_for_text = str(extra.parent)
                self.__config_save()
                self.__collect_new_words()
                self.__send_to_ui(CoreMsg.TEXT_LOADED)

            case UiMsg.DROP_TEXT:
                self.__text.drop()
                self.__names_queue.clear()
                self.__words_queue.clear()
                self.__send_to_ui(CoreMsg.TEXT_DROPED)

            case UiMsg.UI_QUEUE_SELECT:
                self.__current_queue = extra

            case UiMsg.UI_QUEUE_VIEW_SELECT:
                if self.__current_queue == 0:
                    self.__words_queue_view = extra
                elif self.__current_queue == 1:
                    self.__names_queue_view = extra

            case UiMsg.UI_QUEUE_SORT_SELECT:
                if self.__current_queue == 0:
                    match extra:
                        case QueueOrder.BY_ALPHABET:
                            self.__words_queue.sort_by_alphabet()
                        case QueueOrder.BY_ALPHABET_REVERSE:
                            self.__words_queue.sort_by_alphabet(reverse=True)
                        case QueueOrder.BY_COUNT:
                            self.__words_queue.sort_by_count()
                        case QueueOrder.BY_COUNT_REVERSE:
                            self.__words_queue.sort_by_count(reverse=True)
                        case QueueOrder.BY_LENGTH:
                            self.__words_queue.sort_by_length()
                        case QueueOrder.BY_LENGTH_REVERSE:
                            self.__words_queue.sort_by_length(reverse=True)
                        case QueueOrder.BY_POSITION:
                            self.__words_queue.sort_by_position()
                        case QueueOrder.BY_POSITION_REVERSE:
                            self.__words_queue.sort_by_position(reverse=True)
                elif self.__current_queue == 1:
                    match extra:
                        case QueueOrder.BY_ALPHABET:
                            self.__names_queue.sort_by_alphabet()
                        case QueueOrder.BY_ALPHABET_REVERSE:
                            self.__names_queue.sort_by_alphabet(reverse=True)
                        case QueueOrder.BY_COUNT:
                            self.__names_queue.sort_by_count()
                        case QueueOrder.BY_COUNT_REVERSE:
                            self.__names_queue.sort_by_count(reverse=True)
                        case QueueOrder.BY_LENGTH:
                            self.__names_queue.sort_by_length()
                        case QueueOrder.BY_LENGTH_REVERSE:
                            self.__names_queue.sort_by_length(reverse=True)
                        case QueueOrder.BY_POSITION:
                            self.__names_queue.sort_by_position()
                        case QueueOrder.BY_POSITION_REVERSE:
                            self.__names_queue.sort_by_position(reverse=True)

            case UiMsg.NEXT_WORD_POSITION:
                if self.__current_queue == 0:
                    if self.__words_queue.current_word:
                        if self.__current_word_position_index < len(
                            self.__words_queue.current_word.positions
                        ) - 1:
                                self.__current_word_position_index += 1
                        else:
                            self.__current_word_position_index = 0
                    else:
                        self.__current_word_position_index = 0

                elif self.__current_queue == 1:
                    if self.__names_queue.current_word:
                        if self.__current_name_position_index < len(
                            self.__names_queue.current_word.positions
                        ) - 1:
                                self.__current_name_position_index += 1
                        else:
                            self.__current_name_position_index = 0
                    else:
                        self.__current_name_position_index = 0

                self.__send_to_ui(CoreMsg.WORD_POSITION_CHANGED)

            case UiMsg.PREVIOUS_WORD_POSITION:
                if self.__current_queue == 0:
                    if self.__words_queue.current_word:
                        if self.__current_word_position_index > 0:
                                self.__current_word_position_index -= 1
                        else:
                            self.__current_word_position_index = len(
                                self.__words_queue.current_word.positions
                            ) - 1
                    else:
                        self.__current_word_position_index = 0
                elif self.__current_queue == 1:
                    if self.__names_queue.current_word:
                        if self.__current_name_position_index > 0:
                                self.__current_name_position_index -= 1
                        else:
                            self.__current_name_position_index = len(
                                self.__names_queue.current_word.positions
                            ) - 1
                    else:
                        self.__current_name_position_index = 0

                self.__send_to_ui(CoreMsg.WORD_POSITION_CHANGED)

            case UiMsg.ENLARGE_TEXT_FRAGMENT:
                self.__fragment_size += self.__fragment_size_step
                self.__send_to_ui(CoreMsg.TEXT_FRAGMENT_SIZE_CHANGED)

            case UiMsg.REDUCE_TEXT_FRAGMENT:
                self.__fragment_size -= self.__fragment_size_step
                self.__send_to_ui(CoreMsg.TEXT_FRAGMENT_SIZE_CHANGED)

            case UiMsg.SKIP_WORD:
                self.current_queue.goto_next()
                if self.__current_queue == 0:
                    self.__current_word_position_index = 0
                elif self.__current_queue == 1:
                    self.__current_name_position_index = 0
                self.__send_to_ui(CoreMsg.NEXT_WORD)

            case UiMsg.IGNORE_WORD:
                if self.current_queue:
                    self.current_word.status = WordStatus.IGNORED
                self.current_queue.goto_next()
                if self.__current_queue == 0:
                    self.__current_word_position_index = 0
                elif self.__current_queue == 1:
                    self.__current_name_position_index = 0
                self.__send_to_ui(CoreMsg.NEXT_WORD)

            case UiMsg.ADD_WORD_TO_BASE:
                if self.current_queue:
                    self.current_word.status = WordStatus.HANDLED
                self.__dbs[extra].buffer.append(self.current_word)
                self.current_queue.goto_next()
                self.__send_to_ui(CoreMsg.NEXT_WORD)

            case UiMsg.DB_SLOT_ADDED:
                self.__dbs.append(DataBase())
                self.__config_save()

            case UiMsg.DB_SLOT_DELETED:
                self.__dbs.pop(extra)
                self.__config_save()
                self.__send_to_ui(CoreMsg.DB_SLOT_DELETED, extra)

            case UiMsg.LOAD_DB:
                path: Path = extra['path']
                self.__dbs[extra['slot']].load(path)
                self.__dbs[extra['slot']].in_use(True)
                self.__last_dir_for_db = str(path.parent)
                self.__config_save()
                self.__send_to_ui(CoreMsg.DB_LOADED)

            case UiMsg.DROP_DB:
                self.__dbs[extra].drop()
                self.__dbs[extra].in_use(False)
                self.__config_save()
                self.__send_to_ui(CoreMsg.DB_DROPED)

            case UiMsg.DB_IN_USE_STATUS_CHANGED:
                self.__dbs[extra['slot']].in_use(extra['state'])
                self.__config_save()

    def __send_to_ui(self, msg: CoreMsg, extra = None):
        self.ui.ui_receiver(msg, extra)

    def __config_load(self):
        self.__config.load()
        self.__last_dir_for_text = self.__config['last_dir_for_text']
        self.__last_dir_for_db = self.__config['last_dir_for_db']
        # Подтягиваем базы данных
        if self.__config.get('databases'):
            for record in self.__config['databases']:
                db = DataBase()
                self.__dbs.append(db)
                db.in_use(record['in_use'])
                if record['path']:
                    db.load(Path(record['path']))
                self.__send_to_ui(CoreMsg.DB_SLOT_ADDED)
                if record['path']:
                    self.__send_to_ui(CoreMsg.DB_LOADED)

    def __config_save(self):
        self.__config['last_dir_for_text'] = self.__last_dir_for_text
        self.__config['last_dir_for_db'] = self.__last_dir_for_db
        # Заносим базы данных
        self.__config['databases'].clear()
        for db in self.__dbs:
            self.__config['databases'].append({
                'path': str(db.path) if db.path else None,
                'in_use': db.in_use()
            })
        self.__config.save()

    def __collect_new_words(self):
        active_dbs = []
        for db in self.__dbs:
            if db.in_use():
                active_dbs.append(db)

        if self.__text.count_all_words:
            for word in self.__text.unique_words:
                in_dbs = False
                for db in active_dbs:
                    if word in db.words:
                        in_dbs = True
                        break
                if not in_dbs:
                    self.__words_queue.append(word)
            for name in self.__text.unique_names:
                in_dbs = False
                for db in active_dbs:
                    if name in db.words:
                        in_dbs = True
                        break
                if not in_dbs:
                    self.__names_queue.append(name)

    ###