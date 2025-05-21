import logging
from logging.handlers import TimedRotatingFileHandler
import os

log_dir = "log"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "app.log")

handler = TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',
    interval=1,
    backupCount=10,
    encoding='utf-8',
    utc=False
)

handler.suffix = "%Y-%m-%d"

formatter = logging.Formatter(
    fmt="[%(levelname)s] %(asctime)s %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]"
)
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)


def log(msg):
    logger.info(msg)