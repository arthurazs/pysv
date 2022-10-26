import asyncio
import pathlib
import socket
import struct
import sys
from contextlib import suppress
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from typing import Iterator, Sequence


def get_sample() -> "Iterator[Sequence[str]]":
    path = pathlib.Path("data") / "example1.csv"
    with open(path, "r") as csv:
        csv.readline()
        for _ in range(2400):
            data = csv.readline()
            yield data.strip().split(",")


def parse_sample(string_sample: str, voltage: bool = False) -> tuple[int, bytes]:
    sample = int(float(string_sample) * (1_000**voltage))
    return sample, struct.pack("!i", sample) + b"\x00\x00\x00\x00"


def parse_neutral(sample: int) -> bytes:
    return struct.pack("!i", sample) + b"\x00\x00\x20\x00"


def get_sv() -> "Iterator[tuple[float, bytes, bytes]]":
    src_addr = b"\x00\x30\xa7\x22\x8d\x5d"
    dst_addr = b"\x01\x0c\xcd\x04\x00\x01"
    sv_ether = b"\x88\xba"
    app_id = b"\x40\x00"
    length = b"\x00\x63"  # TODO calc?
    reserved = b"\x00\x00\x00\x00"
    sv_type = b"\x60"
    sv_len = b"\x59"  # TODO calc?
    num_asdu = b"\x80\x01\x01"
    seq_asdu_type = b"\xa2"
    seq_asdu_len = b"\x54"  # TODO calc?
    asdu_type = b"\x30"
    asdy_len = b"\x52"  # TODO calc?
    sv_id = b"\x80\x01\x32"
    smp_cnt = b"\x82\x02\x07\x97"  # TODO update
    conf_rev = b"\x83\x04\x00\x00\x00\x01"
    smp_synch = b"\x85\x01\x00"
    phs_meas_type_len = b"\x87\x40"
    for index, timestamp, i_as, i_bs, i_cs, v_as, v_bs, v_cs in get_sample():
        i_ai, i_a = parse_sample(i_as)
        i_bi, i_b = parse_sample(i_bs)
        i_ci, i_c = parse_sample(i_cs)
        i_n = parse_neutral(i_ai + i_bi + i_ci)

        v_ai, v_a = parse_sample(v_as, True)
        v_bi, v_b = parse_sample(v_bs, True)
        v_ci, v_c = parse_sample(v_cs, True)
        v_n = parse_neutral(v_ai + v_bi + v_ci)
        smp_cnt = b"\x82\x02" + struct.pack("!h", int(index))

        yield (
            float(timestamp),
            dst_addr
            + src_addr
            + sv_ether
            + app_id
            + length
            + reserved
            + sv_type
            + sv_len
            + num_asdu
            + seq_asdu_type
            + seq_asdu_len
            + asdu_type
            + asdy_len
            + sv_id
            + smp_cnt
            + conf_rev
            + smp_synch,
            phs_meas_type_len + i_a + i_b + i_c + i_n + v_a + v_b + v_c + v_n,
        )


async def run(loop: AbstractEventLoop, send: int) -> None:
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, 0xBA88) as nic:
        nic.bind(("lo", 0))
        nic.setblocking(False)

        if send:
            next_timestamp = -300.0
            for timestamp, header, pdu in get_sv():
                if timestamp < next_timestamp:
                    continue
                # TODO Improve sleeping
                elapsed = loop.time()
                while ((loop.time() - elapsed) * 1_000_000) < 208.333:
                    await asyncio.sleep(0)
                # await asyncio.sleep(max(loop.time() - elapsed, 0))
                await loop.sock_sendall(nic, header + pdu)
                next_timestamp = timestamp + 0.208333
        else:
            count = 0
            while True:
                elapsed = loop.time()
                data = await loop.sock_recv(nic, 113)
                data = data[47 + 2 :]
                i_a, _, i_b, _, i_c, _, i_n, _ = struct.unpack("!8i", data[: 8 * 4])
                v_a, _, v_b, _, v_c, _, v_n, _ = struct.unpack("!8i", data[8 * 4 :])
                print(
                    f"{count}: {(loop.time() - elapsed) * 1_000_000:.3f} us |"
                    f" ia {i_a:4} | ib {i_b:4} | ic {i_c:4} | in {i_n:4} |<>|"
                    f" va {v_a:4} | vb {v_b:4} | vc {v_c:4} | vn {v_n:4}"
                )
                count += 1


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    with suppress(KeyboardInterrupt):
        loop.run_until_complete(run(loop, int(sys.argv[1])))
    loop.close()
