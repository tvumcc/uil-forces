import logging

log = logging.getLogger(__name__)
console_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "[{asctime}] {funcName} - {levelname}: {message}",
    style="{",
    datefmt="%Y/%m/%d %H:%M:%S",
)

log.addHandler(console_handler)
console_handler.setFormatter(formatter)
log.setLevel(logging.INFO)