# Python libs
from pathlib import Path
import json


class Config(dict):
    # Неизменяемый путь к конфигу
    __config_path: Path = Path('abooktools.config')
    def __init__(self):
        super().__init__()

    def load(self):

        if self.__config_path.is_file():
            try:
                data = self.__config_path.read_text(encoding='utf-8')
            except Exception as error:
                raise Exception(error, 'Проблема при чтении конфига')
            data = json.loads(data)
            self.update(data)
        else:
            self.__config_path.touch()

    def save(self):
        self.__config_path.write_text(json.dumps(self), encoding='utf-8')