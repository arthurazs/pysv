import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=os.getenv("PYSV_LOG_LEVEL", "INFO"))
