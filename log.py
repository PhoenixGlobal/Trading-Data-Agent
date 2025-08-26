import logging
from logging.handlers import TimedRotatingFileHandler
import os
import re
import datetime

log_dir = "log"
os.makedirs(log_dir, exist_ok=True)
base_log_filename = "app.log"
log_file = os.path.join(log_dir, base_log_filename)

handler = TimedRotatingFileHandler(
    filename=log_file,
    when='midnight',
    interval=1,
    backupCount=10,
    encoding='utf-8',
    utc=True
)

handler.suffix = "%Y-%m-%d"

formatter = logging.Formatter(
    fmt="[%(levelname)s] %(asctime)s %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]"
)
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def log(msg):
    logger.info(msg)


def clean_old_logs():
    log_files = os.listdir(log_dir)
    pattern = re.compile(re.escape(base_log_filename) + r"\.(\d{4}-\d{2}-\d{2})")

    today = datetime.date.today()
    for filename in log_files:
        match = pattern.match(filename)
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                age = (today - file_date).days
                if age > 10:
                    path = os.path.join(log_dir, filename)
                    print(f"Deleting old log file: {path}")
                    log(f"Deleting old log file: {path}")
                    os.remove(path)
            except Exception as e:
                print(f"Error parsing date from filename {filename}: {e}")
                log(f"Error parsing date from filename {filename}: {e}")


clean_old_logs()
