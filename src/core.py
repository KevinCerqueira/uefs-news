from dotenv import load_dotenv
import platform
import os
from datetime import datetime, date


class Log:

    level: str

    def __init__(self, origin: str = "any") -> None:
        load_dotenv()
        self.origin = origin
        self.path_log = '/tmp/logs/log_'
        if platform.system() not in ['Linux', 'Darwin']:
            self.path_log = '\\tmp\\logs\\log_'
        self.level = os.getenv("LOG_LEVEL")

    def register(self, level: str, msg: str) -> None:
        if not os.path.exists('tmp/logs'):
            os.makedirs('tmp/logs')
        with open(
                os.path.dirname(os.path.realpath(__file__)) + self.path_log + str(date.today()) + '.log', 'a',
                encoding='utf-8'
        ) as log_file:
            log_file.write("[{}] {}: {} \n".format(str(datetime.now()), level, msg))

    def error(self, msg: str) -> None:
        self.register('ERROR', self.origin + " - " + msg)

    def info(self, msg: str) -> None:
        if self.level != "error":
            self.register('INFO', self.origin + " - " + msg)

    def debug(self, msg: str) -> None:
        if self.level == "debug":
            self.register('DEBUG', self.origin + " - " + msg)


class Core:
    log: Log
    origin: str

    def __init__(self, origin: str):
        load_dotenv()
        self.origin = origin
        self.log = self.get_logger()

    def get_logger(self) -> Log:
        return Log(self.origin)
