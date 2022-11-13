from asyncio import sleep
from time import time_ns


def usleep(microseconds: int) -> None:
    end = time_ns() + (microseconds * 1e3)
    while True:
        if time_ns() >= end:
            break


async def async_usleep(microseconds: int) -> None:
    end = time_ns() + (microseconds * 1e3)
    while True:
        await sleep(0)
        if time_ns() >= end:
            break
