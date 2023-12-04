import logging
import os
import sys
from contextlib import suppress
from pathlib import Path

from uvloop import new_event_loop

from pysv import publisher_async as async_pub, subscriber_async as async_sub

logger = logging.getLogger(__name__)

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
loop.close()
