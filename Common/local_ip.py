from Common.config import LISTEN_ONLY_ON_LOCALHOST
import socket

local_ip = "127.0.0.1"
if not LISTEN_ONLY_ON_LOCALHOST:
    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        temp_socket.connect(("10.255.255.255", 1))
        local_ip = temp_socket.getsockname()[0]
    except socket.error:
        local_ip = "127.0.0.1"
        exit()
    finally:
        temp_socket.close()

print(local_ip)
