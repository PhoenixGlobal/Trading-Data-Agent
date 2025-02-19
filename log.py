import logging
LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s  %(message)s "
DATE_FORMAT = '[%Y-%m-%d %H:%M:%S] '

logging.basicConfig(level=logging.DEBUG,
                    format=LOG_FORMAT,
                    datefmt = DATE_FORMAT ,
                    filename="./log/test.log"
                    )


def log(msg):
    logging.info(msg)