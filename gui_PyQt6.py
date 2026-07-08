# Python libs
from pathlib import Path
import traceback
from collections import ChainMap


# Project files
from class_Core import Core
from class_DataBase import DataBase
from messages import UiMsg, CoreMsg
from class_Word import Word, WordStatus
from class_Queue import QueueView, QueueOrder


# PyQt6 or PySide6 lib files
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow,
        QFileDialog, QMessageBox, QDialog, QFormLayout,
        QWidget, QTabWidget, QGroupBox, QFrame, QScrollArea,
        QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QCheckBox, QListWidgetItem,
        QVBoxLayout, QHBoxLayout,
        QSizePolicy,
    )
    
    from PyQt6.QtCore import (
        Qt, QSize, QMargins
    )
    from PyQt6.QtGui import QColor, QFont, QTextCharFormat
except ModuleNotFoundError:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow,
        QFileDialog, QMessageBox, QDialog, QFormLayout,
        QWidget, QTabWidget, QGroupBox, QFrame, QScrollArea,
        QPushButton, QLabel, QLineEdit, QTextEdit, QListWidget, QCheckBox, QListWidgetItem,
        QVBoxLayout, QHBoxLayout,
        QSizePolicy,
    )
    
    from PySide6.QtCore import (
        Qt, QSize, QMargins
    )
    from PySide6.QtGui import QColor, QFont, QTextCharFormat


class LoadTextGroup(QWidget):
    '''
    Группировка элементов отвечающих за загрузку текста
    ----------------------------------------------------
    | drop_text_file | text_file_path | load_text_file |
    |--------------------------------------------------|
    | text_statistics                                  |
    ----------------------------------------------------
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        # КНОПКА сброса загруженного файла
        self.drop_text_file = QPushButton('#')
        self.drop_text_file.setVisible(False)
        self.drop_text_file.setMaximumWidth(30)

        # Текстовое поле для ввода адреса файла
        self.text_file_path = QLineEdit()
        self.text_file_path.setPlaceholderText('выберите файл...')

        # КНОПКА загрузки файла с текстом
        self.load_text_file = QPushButton('Загрузить')

        # Надпись со статистикой по загруженному тексту
        self.text_statistics = QLabel('...текст не загружен...')

        '''Размещаем объекты'''
        line = QHBoxLayout()
        line.addWidget(self.drop_text_file)
        line.addWidget(self.text_file_path)
        line.addWidget(self.load_text_file)

        root.addLayout(line)
        root.addWidget(self.text_statistics)

        '''Подключаем кнопки/события к функциям'''
        # Кнопка загрузки
        self.load_text_file\
            .clicked.connect(self.on_load_text_file_button_clicked)
        # Кнопка сброса
        self.drop_text_file\
            .clicked.connect(self.on_drop_text_file_button_clicked)

    def on_load_text_file_button_clicked(self):
        file_path = self.text_file_path.text()
            # или из диалогового окна
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                'Выберите текстовый файл',
                None,
                'utf-8 text (*.txt)'
            )
        if file_path:
            try:
                self.parent().send_to_core(UiMsg.LOAD_TEXT, Path(file_path))
            except Exception:
                self.show_error(traceback.format_exc())
            else:
                self.text_file_path.setText(str(file_path))
                self.text_file_path.setReadOnly(True)
                self.load_text_file.setVisible(False)
                self.drop_text_file.setVisible(True)
                t = f'Символов: {self.core.text.length}  |  '
                t+= f'Слов: {self.core.text.count_all_words}/'
                t+= f'{self.core.text.count_unique_words \
                    + self.core.text.count_unique_names}('
                t+= f'{self.core.text.count_unique_words}/'
                t+= f'{self.core.text.count_unique_names}) '
                t+= f'(всего/уник.(сл/им))'
                self.text_statistics.setText(t)

    def on_drop_text_file_button_clicked(self):
        self.send_to_core(UiMsg.DROP_TEXT)
        self.text_file_path.setText('')
        self.text_file_path.setReadOnly(False)
        self.load_text_file.setVisible(True)
        self.drop_text_file.setVisible(False)
        self.text_statistics.setText('...текст не загружен...')


class QueueTab(QWidget):
    '''
    Вкладка с очередью слов
    Содержит/выполняет:
    - прокручиваемый список слов
    - 4 кнопки задающие какие слова показывать
        - все
        - только необработанные
        - только обработанные
        - только игнорируемые
    - 8 кнопок сортировки порядка слов
        - по алфавиту (прямая/обратная)
        - по количеству нахождений слова (больше/меньше)
        - по длине слова (длинее/короче)
        - по позиции первого нахождения слова в тексте
          (с начала в конец/из конца в начало)
    --------------------------
    | sort_buttons (x6)      |
    --------------------------
    | list (word queue)      |
    --------------------------
    | show_mode_buttons (x4) |
    --------------------------
    | statistics             |
    --------------------------
    '''
    def __init__(self, parent: QWidget, tabs_container: QTabWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        # КНОПКИ сортировки
        self.sort_buttons = {
            'by_alphabet': QPushButton('А-Я'),
            'by_alphabet_reverse': QPushButton('Я-А'),
            'by_count': QPushButton('..'),
            'by_count_reverse': QPushButton(':::'),
            'by_length': QPushButton('. ...'),
            'by_length_reverse': QPushButton('... .'),
            'by_position': QPushButton('1,2'),
            'by_position_reverse': QPushButton('2,1'),
        }
        # КНОПКИ режима отображения списка
        self.show_mode_buttons = {
            'all': QPushButton('.'),
            'pending': QPushButton('?'),
            'handled': QPushButton('v'),
            'ignored': QPushButton('x'),
        }
        # Параметры кнопок
        for _, button in ChainMap(
            self.sort_buttons,
            self.show_mode_buttons
        ).items():
            button.setMinimumWidth(40)

        # Статистика работы со словами
        self.statistics = QLabel(f'Обработано: 0\nИсключены: 0\nОсталось: 0')

        # Список слов
        self.list = QListWidget()

        '''Размещаем объекты'''
        top = QHBoxLayout()
        for _, button in self.sort_buttons.items():
            top.addWidget(button)

        bottom = QHBoxLayout()
        for _, button in self.show_mode_buttons.items():
            bottom.addWidget(button)

        root.addLayout(top)
        root.addWidget(self.list)
        root.addLayout(bottom)
        root.addWidget(self.statistics)

        '''Подключаем кнопки/события к функциям'''
        # Кнопки сортировки
        for name, button in self.sort_buttons.items():
            button.clicked.connect(lambda checked, n=name: self.on_sort_button_clicked(n))

        # Кнопки режима отображения списка
        for name, button in self.show_mode_buttons.items():
            button.clicked.connect(lambda checked, n=name: self.on_show_mode_button_clicked(n))

    def on_sort_button_clicked(self, button_name):
        match button_name:
            case 'by_alphabet':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_ALPHABET
                )
            case 'by_alphabet_reverse':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_ALPHABET_REVERSE
                )
            case 'by_count':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_COUNT
                )
            case 'by_count_reverse':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_COUNT_REVERSE
                )
            case 'by_length':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_LENGTH
                )
            case 'by_length_reverse':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_LENGTH_REVERSE
                )
            case 'by_position':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_POSITION
                )
            case 'by_position_reverse':
                self.send_to_core(
                    UiMsg.UI_QUEUE_SORT_SELECT,
                    QueueOrder.BY_POSITION_REVERSE
                )
        self.refresh()

    def on_show_mode_button_clicked(self, button_name):
        match button_name:
            case 'all':
                self.send_to_core(
                    UiMsg.UI_QUEUE_VIEW_SELECT,
                    QueueView.ALL
                )
            case 'pending':
                self.send_to_core(
                    UiMsg.UI_QUEUE_VIEW_SELECT,
                    QueueView.PENDING
                )
            case 'handled':
                self.send_to_core(
                    UiMsg.UI_QUEUE_VIEW_SELECT,
                    QueueView.HANDLED
                )
            case 'ignored':
                self.send_to_core(
                    UiMsg.UI_QUEUE_VIEW_SELECT,
                    QueueView.IGNORED
                )
        self.refresh()

    def refresh(self):
        self.list.clear()
        for i, word in enumerate(self.core.current_queue_view):
            t = f'{word}'
            t+= f' ({len(word.positions)})'
            match word.status:
                case WordStatus.HANDLED:
                    t += ' v'
                    color = QColor(0,255,0)
                case WordStatus.IGNORED:
                    t += ' x'
                    color = QColor(255,0,0)
                case WordStatus.PENDING:
                    color = QColor(0,0,0)
            self.list.addItem(t)
            self.list.item(i).setForeground(color)
            if word == self.core.current_word:
                self.list.setCurrentRow(i)

        t = f'Обработано: {self.core.current_queue.count_handled}\n'
        t+= f'Исключены: {self.core.current_queue.count_ignored}\n'
        t+= f'Осталось: {self.core.current_queue.count_pending}'
        self.statistics.setText(t)


class TextFragmentGroup(QWidget):
    '''
    Группировка элементов для работы с текущим словом
    и его текстовыми фрагментами
        - кнопки переключения позиций слова в тексте
        - кнопки увеличения/уменьшения фрагмента
    
        |<| слово |>|   |+| |-|
        -----------------------
        | фрагмент текста     |
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        # КНОПКА перехода к предыдущей позиции слова
        self.prev_word_pos = QPushButton('<')
        self.prev_word_pos.setMaximumWidth(40)

        # КНОПКА перехода к следующей позиции слова
        self.next_word_pos = QPushButton('>')
        self.next_word_pos.setMaximumWidth(40)

        # Текущее слово
        self.current_word = QLabel('<нет подходящего слова>')

        # КНОПКА увеличения фрагмента текста
        self.enlarge_text_fragment = QPushButton('+')
        self.enlarge_text_fragment.setMaximumWidth(40)

        # КНОПКА уменьшения фрагмента текста
        self.reduce_text_fragment = QPushButton('-')
        self.reduce_text_fragment.setMaximumWidth(40)

        # Фрагмент текста
        self.text_fragment = QTextEdit()
        self.text_fragment.setPlaceholderText('текст не загружен')
        self.text_fragment.setReadOnly(True)

        '''Размещаем объекты'''
        line = QHBoxLayout()
        line.addWidget(self.prev_word_pos)
        line.addWidget(self.current_word)
        line.addWidget(self.next_word_pos)
        line.addStretch()
        line.addWidget(self.reduce_text_fragment)
        line.addWidget(self.enlarge_text_fragment)

        root.addLayout(line)
        root.addWidget(self.text_fragment)

        '''Подключаем кнопки/события к функциям'''
        # Кнопка предыдущей позиции слова
        self.prev_word_pos.clicked.connect(
            lambda: self.send_to_core(UiMsg.PREVIOUS_WORD_POSITION)
        )
        # Кнопка следующей позиции слова
        self.next_word_pos.clicked.connect(
            lambda: self.send_to_core(UiMsg.NEXT_WORD_POSITION)
        )

        # Кнопка увеличения фрагмента текста
        self.enlarge_text_fragment.clicked.connect(
            lambda: self.send_to_core(UiMsg.ENLARGE_TEXT_FRAGMENT)
        )

        # Кнопка уменьшения фрагмента текста
        self.reduce_text_fragment.clicked.connect(
            lambda: self.send_to_core(UiMsg.REDUCE_TEXT_FRAGMENT)
        )

    def refresh(self):
        if self.core.current_word:
            t = f'{self.core.current_word}'
            t+= f' ({self.core.current_word_position_index + 1}/'
            t+= f'{len(self.core.current_word.positions)})'
            self.current_word.setText(t)

            fragment_before = self.core.fragment_before(
                self.core.current_word_position,
                len(self.core.current_word),
                self.core.fragment_size
            )
            raw_word = self.core.current_word_raw
            fragment_after = self.core.fragment_after(
                self.core.current_word_position,
                len(self.core.current_word),
                self.core.fragment_size
            )

            fragment_format = QTextCharFormat()
            fragment_format.setBackground(QColor(255,255,255))
            fragment_format.setFontWeight(QFont.Weight.Normal)

            word_format = QTextCharFormat()
            word_format.setBackground(QColor(0,255,0))
            word_format.setFontWeight(QFont.Weight.Bold)

            self.text_fragment.clear()
            self.text_fragment.textCursor().\
                insertText(fragment_before, fragment_format)
            self.text_fragment.textCursor().\
                insertText(raw_word, word_format)
            self.text_fragment.textCursor().\
                insertText(fragment_after, fragment_format)

        else:
            self.current_word.setText('<нет подходящего слова>')
            self.text_fragment.setText('')


class DecisionButtonsGroup(QWidget):
    '''
    Динамически создающиеся кнопки для отправки слова в какую-либо базу
    (кнопки привязываются к загруженным слотам баз)
        - добавить в базу <...>
    Также есть две статические кнопки
        - пропустить
        - игнорировать
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        # КНОПКА "пропустить"
        self.skip = QPushButton('Пропустить')

        # КНОПКА "игнорировать"
        self.ignore = QPushButton('Игнорировать')

        # КНОПКИ добавления в базы
        self.add = {}

        '''Размещаем объекты'''
        line = QHBoxLayout()
        line.addWidget(self.ignore)
        line.addWidget(self.skip)

        self.db_layout = QVBoxLayout()

        root.addLayout(line)
        root.addLayout(self.db_layout)

        '''Подключаем кнопки/события к функциям'''
        self.skip.clicked.connect(lambda: \
            self.send_to_core(UiMsg.SKIP_WORD))
        self.ignore.clicked.connect(lambda: \
            self.send_to_core(UiMsg.IGNORE_WORD))

    def add_db_button(self):
        # Создаём
        key = len(self.add)
        button = QPushButton(f'Слот {key}: база не загружена')
        self.add[key] = button
        # Размещаем
        self.db_layout.addWidget(button)
        # Подключаем к функции
        button.clicked.connect(self.send_to_core(UiMsg.ADD_WORD_TO_BASE, key))

    def refresh(self):
        for button in self.db_layout.children():
            button.setText(
                self.core.database(self.db_layout.indexOf(button)).name
            )


class WorkTab(QWidget):
    '''
    ВКЛАДКА РАБОТЫ СО СЛОВАМИ
    ____________________________
    |     load_file_block      |
    ---------------------------|
    | left_block | right block |
    ----------------------------
    Одна из корневых вкладок окна
    Содержит/выполняет:
    - вкладки с очередями
        - очередь слов
        - очередь имён
    - загрузка текста
    - кнопки сортировки слов в очереди
    - кнопки выбора "слова с каким статусом показывать"
    - текущее слово
    - фрагмент текста
    - кнопки перемещения по позициям текущего слова
      (сменить фрагмент текста)
    - кнопки увеличения/уменьшения фрагмента текста
    - кнопки ИГНОРИРОВАТЬ и ПРОПУСТИТЬ
    - динамически добавляемые кнопки ДОБАВИТЬ В БАЗУ
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        self.load_text_group = LoadTextGroup(self)
        self.tabs = QTabWidget(self)
        self.words_tab = QueueTab(self, self.tabs)
        self.names_tab = QueueTab(self, self.tabs)
        self.text_fragment_group = TextFragmentGroup(self)
        self.decision_buttons_group = DecisionButtonsGroup(self)

        '''Размещаем объекты'''
        self.tabs.addTab(self.words_tab, 'Слова (0)')
        self.tabs.addTab(self.names_tab, 'Имена (0)')

        right = QVBoxLayout()
        right.addWidget(self.text_fragment_group)
        right.addWidget(self.decision_buttons_group)

        double = QHBoxLayout()
        double.addWidget(self.tabs)
        double.addLayout(right)

        root.addWidget(self.load_text_group)
        root.addLayout(double)

        '''Подключаем кнопки/события к функциям'''
        self.tabs.currentChanged.\
            connect(lambda: self.send_to_core(
                UiMsg.UI_QUEUE_SELECT,
                self.tabs.currentIndex()
            ))
        self.tabs.currentChanged.connect(self.words_tab.refresh)
        self.tabs.currentChanged.connect(self.names_tab.refresh)
        self.tabs.currentChanged.connect(self.text_fragment_group.refresh)

    def refresh(self):
        self.tabs.setTabText(0, f'Слова ({self.core.count_words})')
        self.tabs.setTabText(1, f'Имена ({self.core.count_names})')


class WordsToSaveTab(QWidget):
    '''
    ВКЛАДКА СО СЛОВАМИ ОТОБРАННЫМИ В БАЗЫ
    Одна из корневых вкладок окна
    Содержит/выполняет:
    - списки добавленных слов для каждой из баз
    - сохранить внесённые слова в выбранную базу
    - переместить слово в список кандидатов другой базы
    - вернуть слово в очередь обработки
    - отредактировать слово
    - просмотр полной конфигурации по каждому слову
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        pass


class DataBaseSlot(QWidget):
    '''
    Сгруппированные элементы для работы с добавлением баз данных
    - текстовое поле для пути
    - кнопка загрузить
    - кнопка убрать слот
    - кнопка сбросить загруженную базу
    - чек-бокс - флаг использования базы
    - надписи: имя, информация
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        # Настройка корневого лейаута
        root.setAlignment(Qt.AlignmentFlag.AlignTop)
        root.setContentsMargins(QMargins(0,0,0,0))

        # Надпись с именем базы
        self.db_name = QLabel()
        self.db_name.setVisible(False)

        # Информация по базе данных (сколько в ней слов)
        self.db_description = QLabel('...база не загружена...')

        # Текстовое поле для ввода пути к файлу базы
        self.db_path = QLineEdit()
        self.db_path.setPlaceholderText('путь к файлу...')

        # КНОПКА загрузки базы слов
        self.load_db = QPushButton('Загрузить')

        # КНОПКА для сброса (изменения) загруженной базы
        self.drop_db = QPushButton('#')
        self.drop_db.setMaximumWidth(30)
        self.drop_db.setVisible(False)

        # КНОПКА для удаления текущего слота с базой слов
        self.delete_db_slot = QPushButton('-')
        self.delete_db_slot.setMaximumWidth(30)

        # Чек-бокс использовать ли слова базы при анализе текста
        self.in_use = QCheckBox('Использовать')

        '''Размещаем объекты'''
        line1 = QHBoxLayout()
        line1.addWidget(self.drop_db)
        line1.addWidget(self.db_path)
        line1.addWidget(self.load_db)
        line1.addWidget(self.db_name)

        line2 = QHBoxLayout()
        line2.addWidget(self.delete_db_slot)
        line2.addStretch()
        line2.addWidget(self.db_description)
        line2.addStretch()
        line2.addWidget(self.in_use)

        root.addLayout(line1)
        root.addLayout(line2)

        '''Подключаем кнопки/события к функциям'''
        self.load_db.clicked.connect(self.on_button_load_db_clicked)
        self.drop_db.clicked.connect(self.on_button_drop_db_clicked)
        self.delete_db_slot.clicked.connect(
            self.on_button_delete_db_slot_clicked
        )


    def on_button_load_db_clicked(self):
        file_path = self.db_path.text()
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                'Выберите файл базы данных',
                None,
                'abooktools DB (*.abtdb)'
            )
        if file_path:
            try:
                pass
            except Exception:
                self.show_error(traceback.format_exc())
            else:
                self.db_name.setVisible(True)
                self.db_name.setText('<без имени>')

                t = f'Слов: {0} | '
                t+= f'{0}'
                t+= f' {0}'
                self.db_description.setText(t)

                self.load_db.setVisible(False)
                self.drop_db.setVisible(True)

                self.db_path.setText(str(file_path))
                self.db_path.setReadOnly(True)

                self.in_use.setChecked(True)

    def on_button_drop_db_clicked(self):
        self.db_name.setVisible(False)
        self.db_name.setText('')
        self.db_path.setText('')
        self.db_path.setReadOnly(False)
        self.db_description.setText('...база не загружена')
        self.load_db.setVisible(True)
        self.drop_db.setVisible(False)
        self.in_use.setChecked(False)

    def on_button_delete_db_slot_clicked(self):
        self.deleteLater()


class ConfigTab(QWidget):
    '''
    ВКЛАДКА С ЗАГРУЖЕННЫМИ БАЗАМИ И ПРОЧЕЙ КОНФИГУРАЦИЕЙ
    Одна из корневых вкладок окна
    Содержит/выполняет:
    - добавить/убрать слот с базой данных
    - загружать/выгружать базы
    - включать/выключать использование
      базы при сканировании текста
    - создавать новую пустую базу
    '''
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        root = QVBoxLayout(self)
        self.core: Core = self.parent().core
        self.send_to_core = self.parent().send_to_core
        self.show_error = self.parent().show_error

        '''Создаём объекты, задаём параметры'''
        # Прокручиваемая область со слотами баз
        db_slots_widget = QWidget(self)
        self.db_slots = QVBoxLayout(db_slots_widget)
        self.db_slots.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.db_slots.setSpacing(20)

        scroll = QScrollArea()
        scroll.setWidget(db_slots_widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        # КНОПКА добавления слота
        add_db_slot = QPushButton('Добавить слот базы')

        # КНОПКА создания новой пустой базы
        create_db = QPushButton('Создать пустую базу')

        '''Размещаем объекты'''
        line = QHBoxLayout()
        line.addWidget(add_db_slot)
        line.addWidget(create_db)

        root.addWidget(scroll)
        root.addLayout(line)

        '''Подключаем кнопки/события к функциям'''
        add_db_slot.clicked.connect(self.create_db_slot)


    def create_db_slot(self):
        '''
        Создание слота для загрузки базы данных
        '''
        self.db_slots.addWidget(DataBaseSlot(self))

    def create_empty_db(self):
        '''
        Создать по выбранному пути файл с новой пустой базой
        '''

        pass


class MainWindow(QMainWindow):
    '''
    Корневое окно программы
    Основная логика GUI
    '''
    def __init__(self, application):
        super().__init__()
        self.application = application

        self.core: Core = Core()
        self.core.ui = self

        self.init_widgets()
        self.show()
        self.application.exec()

    def init_widgets(self):
        self.setWindowTitle('ABookTools dev')
        self.setGeometry(0, 0, 800, 600)
        self.setCentralWidget(QTabWidget())
        self.centralWidget().setLayout(QVBoxLayout())

        '''Создаём объекты, задаём параметры'''
        self.work_tab = WorkTab(self)
        self.words_to_save_tab = WordsToSaveTab(self)
        self.config_tab = ConfigTab(self)

        '''Размещаем объекты'''
        self.centralWidget().addTab(self.work_tab, 'Обработка слов')
        self.centralWidget().\
            addTab(self.words_to_save_tab, 'Сохранение слов в базы')
        self.centralWidget().addTab(self.config_tab, 'Конфигурация')

    def ui_receiver(self, msg: CoreMsg, extra = None):
        match msg:
            case CoreMsg.TEST:
                self.show_error(Exception(CoreMsg.TEST.value))

            case CoreMsg.TEXT_LOADED:
                self.work_tab.words_tab.refresh()
                self.work_tab.names_tab.refresh()
                self.work_tab.text_fragment_group.refresh()
                self.work_tab.refresh()

            case CoreMsg.TEXT_DROPED:
                self.work_tab.words_tab.refresh()
                self.work_tab.names_tab.refresh()
                self.work_tab.text_fragment_group.refresh()
                self.work_tab.refresh()

            case CoreMsg.WORD_POSITION_CHANGED:
                self.work_tab.text_fragment_group.refresh()

            case CoreMsg.TEXT_FRAGMENT_SIZE_CHANGED:
                self.work_tab.text_fragment_group.refresh()

            case CoreMsg.DB_SLOT_ADDED:
                self.work_tab.decision_buttons_group.add_db_button()

            case CoreMsg.DB_LOADED:
                self.work_tab.decision_buttons_group.refresh()

            case CoreMsg.NEXT_WORD:
                self.work_tab.text_fragment_group.refresh()
                self.work_tab.words_tab.refresh()
                self.work_tab.names_tab.refresh()

    def send_to_core(self, msg: UiMsg, extra = None):
        self.core.core_receiver(msg, extra)

    def show_error(self, error: Exception):
        '''
        Показывает окно с информацией об ошибке
        '''
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle('Ошибка')
        msg.setText('ОШИБКА!')
        msg.setInformativeText(str(error))
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()


if __name__ == '__main__':
    mainWindow = MainWindow(QApplication([]))
