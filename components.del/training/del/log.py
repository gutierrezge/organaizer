import kivy
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s.%(funcName)s at %(lineno)d - %(message)s",
)
# kivy.config.Config.set('kivy', 'log_level', 'error')
# logging.getLogger('kivy').setLevel(logging.ERROR)
# logging.getLogger('matplotlib').setLevel(logging.ERROR)
# logging.getLogger('ultralytics').setLevel(logging.ERROR)
# logging.getLogger('PIL').setLevel(logging.ERROR)
# logging.getLogger('asyncio').setLevel(logging.ERROR)
# logging.getLogger('werkzeug').setLevel(logging.ERROR)