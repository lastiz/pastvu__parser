import logging
from logging import StreamHandler, Formatter

logger = logging.getLogger("main")
logger.setLevel(logging.INFO)

handler = StreamHandler()
handler.setFormatter(
    Formatter(
        fmt="[%(asctime)s  %(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
)
logger.addHandler(handler)
