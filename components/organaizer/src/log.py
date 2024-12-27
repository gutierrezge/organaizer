import logging
import logging.handlers
import warnings
from typing import Union

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger("apscheduler").setLevel(logging.ERROR)

# LOG_FILENAME='console.log'
LOG_FILENAME = None
BACKUP_COUNT = 5
LOG_FILE_MAX_BYTES = 1*1024*1024
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s"


def configure():
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logger = logging.getLogger()

    if LOG_FILENAME is not None:
        logger.handlers.clear()
        handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=LOG_FILE_MAX_BYTES, backupCount=BACKUP_COUNT)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
    
    return logger


def app_print(logger, text:Union[str, list[str]], border_char:str="#", width:int=60):
    texts:list[str] = text if isinstance(text, list) else [text]
    border:str = border_char * width
    logger.info(border)
    for t in texts:
        logger.info(f"{border_char}{t.center(width - 2)   }{border_char}")
    logger.info(border)