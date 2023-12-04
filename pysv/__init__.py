import logging
import os

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

log_level = os.getenv("PYSV_LOG_LEVEL")

if log_level:
    logger.setLevel(log_level)
