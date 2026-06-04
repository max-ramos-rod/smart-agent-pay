import sys
from loguru import logger


def setup_logging() -> None:
    logger.remove()

    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    logger.add(
        "logs/sentinelfi.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
    )

    logger.add(
        "logs/errors.log",
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}\n{exception}",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )
