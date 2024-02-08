import logging
import os
import sys
from contextlib import suppress
from pathlib import Path

try:
    from uvloop import new_event_loop
except ImportError:
    from asyncio import get_event_loop as new_event_loop

from pysv import publisher_async as async_pub
from pysv import subscriber_async as async_sub
import pysv.c_package as c_pub

logging.basicConfig(format="[%(levelname)7s] %(asctime)s | %(name)20s:%(lineno)4d > %(message)s")
logger = logging.getLogger("pysv")

interface = os.environ["PYSV_INTERFACE"]

loop = new_event_loop()
if "-ap" in sys.argv:
    try:
        csv_path = Path(sys.argv[2])
    except IndexError:
        csv_path = Path(os.environ["PYSV_CSV_FILE"])
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(async_pub.run(loop, interface, csv_path))
elif "-as" in sys.argv:
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(async_sub.run(loop, interface))
elif "-debug" in sys.argv:
    logger.info("Starting c_pub...")
    c_pub.publisher_busy_smart(interface, Path(os.environ["PYSV_CSV_FILE"]))
    logger.info("Done!")
loop.close()
