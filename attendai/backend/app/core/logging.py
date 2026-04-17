import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    logger.remove()
    logger.add(sys.stdout, level=settings.LOG_LEVEL, colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>")
    logger.add("logs/attendai.log", rotation="50 MB", retention="30 days",
               level="INFO", encoding="utf-8")
