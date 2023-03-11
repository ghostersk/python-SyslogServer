import socket
import time
from datetime import datetime

# IP of the server, as I run it on same PC i used loopback
UDP_IP = '127.0.0.1'
UDP_PORT = 514

for x in range(100):
    current_time = datetime.now()
    MESSAGE = f"<150>Mar {current_time} Vigor3900: Local User: (MAC=68:4f:64:97:6b:95)       10.2.12.30:60073 -> 20.190.159.23:443 (UDP)"
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(bytes(MESSAGE, 'utf-8'), (UDP_IP, UDP_PORT))
    sock.close()
    time.sleep(0.1)
