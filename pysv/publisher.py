import socket
import sys


def run(send: int) -> None:
    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, 0x300) as nic:
        nic.bind(("lo", 0))
        nic.setblocking(False)

        src_addr = b"\x01\x02\x03\x04\x05\x06"
        dst_addr = src_addr
        header = src_addr + dst_addr

        if send:
            print("sending")
            nic.sendall(header + b"arthur")
            print("sent")
        else:
            count = 0
            while True:
                try:
                    print(count, nic.recv(len(header) + 6))
                except BlockingIOError:
                    continue
                count += 1


if __name__ == "__main__":
    run(int(sys.argv[1]))
