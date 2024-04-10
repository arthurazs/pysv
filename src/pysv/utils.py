from asyncio import sleep
from struct import pack
from time import time_ns

MAC_LEN_WITH_SPLITTER = 17


def enet_stom(mac_address: str) -> bytes:
    """MAC Address from string to bytes."""
    if len(mac_address) == MAC_LEN_WITH_SPLITTER:
        splitter = mac_address[2]  # probably one of these: " ", "-", ":"
        mac_address = mac_address.replace(splitter, "")
    return pack("!Q", int(mac_address, 16))[2:]  # mac is 6 bytes long, Q generates 8 bytes


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
