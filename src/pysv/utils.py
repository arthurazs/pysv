from asyncio import sleep
from time import time_ns
from struct import pack


def enet_stom(mac_address: str) -> bytes:
    """MAC Address from string to bytes."""
    if len(mac_address) == 17:
        splitter = mac_address[2]  # probably one of these: " ", "-", ":"
        mac_address = mac_address.replace(splitter, "")
    return pack("!Q", int(mac_address, 16))


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
