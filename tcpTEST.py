import socket
import time
from datetime import datetime

# Here you can define IP of your syslog server
TCP_IP = '127.0.0.1'
TCP_PORT = 514


for x in range(100):
    current_time = datetime.now()
    MESSAGE = f"<150>Mar {current_time} Vigor3900: Local User: (MAC=68:4f:64:97:6b:95)       10.2.12.30:60073 -> 20.190.159.23:443 (TCP)"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TCP_IP, TCP_PORT))
    s.sendall(bytes(MESSAGE, 'utf-8'))
    s.close()
    time.sleep(0.1)
