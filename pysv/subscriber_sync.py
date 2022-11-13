from contextlib import suppress
from itertools import count
from socket import AF_PACKET, SOCK_RAW, socket
from struct import unpack as s_unpack
from sys import argv
from time import time_ns


def run(interface: str) -> None:
    with socket(AF_PACKET, SOCK_RAW, 0xBA88) as nic:
        nic.bind((interface, 0))
        helper = {1: "!B", 2: "!H"}

        for counter in count():
            elapsed = time_ns()
            data = nic.recv(113)
            cnt_len = data[35]
            smp_cnt = s_unpack(helper[cnt_len], data[36 : 36 + cnt_len])[0]
            data = data[47 + 2 :]
            i_a, _, i_b, _, i_c, _, i_n, _ = s_unpack("!8i", data[: 8 * 4])
            v_a, _, v_b, _, v_c, _, v_n, _ = s_unpack("!8i", data[8 * 4 :])
            print(
                f"{counter:4}/{smp_cnt:4}: {(time_ns() - elapsed) * 1E-3:13.3f} us |"
                f" ia {i_a:6} | ib {i_b:6} | ic {i_c:6} | in {i_n:6} |<>|"
                f" va {v_a:6} | vb {v_b:6} | vc {v_c:6} | vn {v_n:6}"
            )


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        run(argv[1])
