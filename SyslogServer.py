import logging
import logging.handlers
import socketserver
import threading
import time
from datetime import datetime
import os

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base


LOG_FILE_LOCATION = os.path.join(os.path.dirname(__file__), 'logs')
DB_FILE_NAME = "traffic.db" # set name of the sql database file
LOG_FILE_NAME = "Syslog-Server-Errors.log" # set desired output file name
FILENAME = os.path.join(LOG_FILE_LOCATION,LOG_FILE_NAME)
os.makedirs(os.path.dirname(FILENAME), exist_ok=True)
DATABASE_URI = f"sqlite:///{os.path.join(LOG_FILE_LOCATION,DB_FILE_NAME)}" # set desired database URI

# Here you can put IP addresses what will be allowed to send Syslog messages to the server
ALLOWED_SOURCE = ['10.10.10.254',]

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

# Set up SQLAlchemy
engine = create_engine(DATABASE_URI, pool_size=200, pool_recycle=3600, connect_args={'timeout': 60})
Base = declarative_base()

class Traffic(Base):
    __tablename__ = 'traffic'
    id = Column(Integer, primary_key=True)
    source_ip = Column(String)
    data = Column(String)
    timestamp = Column(DateTime, default=datetime.now())

# Create database table if it doesn't exist
Base.metadata.create_all(engine)

# Set up thread-local SQLAlchemy session
Session = scoped_session(sessionmaker(bind=engine))

class SyslogHandlerUDP(socketserver.BaseRequestHandler):
    def handle(self):
        try:
            source_ip = self.client_address[0]
            if source_ip in ALLOWED_SOURCE:
                data = bytes.decode(self.request[0].strip())
                protocol = 'UDP'
                port = self.server.server_address[1]
                # Save data to database
                traffic = Traffic(source_ip=source_ip, data=data)
                session = Session()
                session.add(traffic)
                session.commit()
            else:
                time_now = datetime.now()
                raise Exception(f"Unauthorized Syslog client data received at: {time_now}")

            logger.info(f'Received {protocol} data from {source_ip} on port {port}: {data}')
        except Exception as e:
            logger.error(f'Error handling request: {e}')
            with open(FILENAME, 'a') as f:
                f.write(f'ERR: {source_ip} -> {e}'.strip() + '\n')

class SyslogHandlerTCP(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            source_ip = self.client_address[0]
            if source_ip in ALLOWED_SOURCE:
                data = self.rfile.readline().decode().strip()
                protocol = 'TCP'
                port = self.server.server_address[1]
                # Save data to database
                traffic = Traffic(source_ip=source_ip, data=data)
                session = Session()
                session.add(traffic)
                session.commit()
            else:
                time_now = datetime.now()
                raise Exception(f"Unauthorized Syslog client data received at: {time_now}")

            logger.info(f'Received {protocol} data from {source_ip} on port {port}: {data}')
        except Exception as e:
            logger.error(f'Error handling request: {e}')
            with open(FILENAME, 'a') as f:
                f.write(f'ERR: {source_ip} -> {e}'.strip() + '\n')

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

def start_servers(tcp_port, udp_port):
    logger.info(f'Starting TCP server on port {tcp_port}')
    tcp_server = ThreadedTCPServer(('0.0.0.0', tcp_port), SyslogHandlerTCP)
    tcp_thread = threading.Thread(target=tcp_server.serve_forever)
    tcp_thread.daemon = True
    tcp_thread.start()

    logger.info(f'Starting UDP server on port {udp_port}')
    udp_server = ThreadedUDPServer(('0.0.0.0', udp_port), SyslogHandlerUDP)
    udp_thread = threading.Thread(target=udp_server.serve_forever)
    udp_thread.daemon = True
    udp_thread.start()

    while True:
        time.sleep(1)

if __name__ == '__main__':
    start_servers(tcp_port=514, udp_port=514)
