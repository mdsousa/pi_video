import socket   #for sockets
import threading
import configparser # read config file
import traceback
import signal
import sys
import errno

import io
import time
import picamera
import struct

server = None
listen_client_socket = None
listen_connection = None
listen_port = None # listen for commands from server
stream_client_socket = None
stream_connection = None
stream_port = None # send image stream to server
stream_write_length = None # how long stream should be saved to disk, in seconds

def signal_handler(signal, frame):
    print("\nCtrl-C pressed")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def readConfig():
    global server
    global listen_port
    global stream_port
    global stream_write_length
    try:
        parser = configparser.ConfigParser()
        parser.read('pi_config.ini')
        server = parser['configuration']['server']
        listen_port = int(parser['configuration']['listen_port'])
        stream_port = int(parser['configuration']['stream_port'])
        stream_write_length = int(parser['camera']['stream_write_length'])
    except configparser.Error as e:
        print(e)
#print(config['configuration'])


class listenNetworkThread(threading.Thread):
    global server
    global listen_port
    def __init__(self, threadID, name, server, lport):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.server = server
        self.listen_port = lport
    def run(self):
        while True:
            try:
#                print(self.listen_port)
                listen_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                listen_client_socket.connect( (self.server, self.listen_port) )
                listen_connect = client_socket.makefile('wb')
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    pass
#                    print("Listen connection refused")

class streamNetworkThread(threading.Thread):
    global server
    global stream_port
    def __init__(self, threadID, name, server, sport):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.server = server
        self.stream_port = sport
    def run(self):
        while True:
            try:
                print(self.stream_port)
                stream_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                stream_client_socket.connect( (self.server, self.stream_port) )
                stream_connect = client_socket.makefile('wb')
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    pass
#                    print("Stream connection refused")
                



def main():
    global server
    global listen_port
    global stream_port
    try:
        readConfig()
        listenNetworkThread1 = listenNetworkThread(1, "listen network thread", server, listen_port)
        listenNetworkThread1.daemon = True
        listenNetworkThread1.start()
        streamNetworkThread1 = streamNetworkThread(1, "stream network thread", server, stream_port)
        streamNetworkThread1.daemon = True
        streamNetworkThread1.start()
        while True:
            time.sleep(100)
    except Exception as e:
        traceback.print_exc()
    finally:
        print("Done")

if __name__ == "__main__":
    main()
