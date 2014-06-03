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
cmd_client_socket = None
cmd_connection = None
cmd_port = None # listen for commands from server
stream_client_socket = None
stream_connection = None
stream_port = None # send image stream to server

stream_write_length = None # how long stream should be saved to disk, in seconds

listening = False # set to True when connection is established
listenForCmdThread = None


def signal_handler(signal, frame):
    print("\nCtrl-C pressed")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def cleanup():
    global cmd_client_socket
    global listening
    if(cmd_client_socket is not None):
        cmd_client_socket.close()
    listening = False
    print("cleaned up")

def readConfig():
    global server
    global cmd_port
    global stream_port
    global stream_write_length
    try:
        parser = configparser.ConfigParser()
        parser.read('pi_config.ini')
        server = parser['configuration']['server']
        cmd_port = int(parser['configuration']['cmd_port'])
#        print("listen_port: %s" % listen_port)
        stream_port = int(parser['configuration']['stream_port'])
        stream_write_length = int(parser['camera']['stream_write_length'])
    except configparser.Error as e:
        print(e)
#print(config['configuration'])


class listenForCmd(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        global listening
        global cmd_client_socket
        print("Listening for cmds on socket: %s" % cmd_client_socket)
        try:
#            cmd_client_socket.listen(0) 
            listening = True
            while listening:
                print("1")
                msg = cmd_client_socket.recv(16).decode('utf-8')
                print(msg)
                if msg == "r":
                    print('record command received')
                elif msg == "s":
                    print('save command received')
                elif msg == "e":
                    listening = False
                    print('e received, exiting')
        except:
            traceback.print_exc(file=sys.stdout)

class listenNetworkThread(threading.Thread):
    def __init__(self, threadID, name, server, lport):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.server = server
        self.cmd_port = lport
    def run(self):
        global listeForCmdThread
        global cmd_client_socket
        while True:
            print("attempt to listen to ip: %s, port: %d" % (self.server, self.cmd_port))
            try:
#                print('server: %s, port %d' % (self.server, self.listen_port))
#                cmd_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cmd_client_socket = socket.socket()
                print("1")
                cmd_client_socket.connect( (self.server, self.cmd_port) )
#                cmd_client_socket.bind( (self.server, self.cmd_port) )
                print("2")
#                cmd_client_socket.listen(0)
#                print("3")
#                listen_connection = cmd_client_socket.accept()
                print("4")
                listenForCmdThread = listenForCmd(1, "listen for cmds")
                listenForCmdThread.daemon = True
                listenForCmdThread.start()
                print('server: %s, port %d connected' % (self.server, self.cmd_port))
#                time.sleep(0.5) # give thread time to breath
                break
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    print('connection error: %s' % e)
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
#                print(self.stream_port)
                stream_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                stream_client_socket.connect( (self.server, self.stream_port) )
                stream_connect = client_socket.makefile('wb')
                break
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    pass
#                    print("Stream connection refused")

def sendStream():
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
                print("streaming")
            except:
                pass


def main():
    global server
    global cmd_port
    global stream_port
    global listenForCmdThread
#    anyInterface = '0.0.0.0'
    try:
        readConfig()
        listenNetworkThread1 = listenNetworkThread(1, "listen network thread", server, cmd_port)
#        listenNetworkThread1 = listenNetworkThread(1, "listen network thread", anyInterface, cmd_port)
        listenNetworkThread1.daemon = True
        listenNetworkThread1.start()
        streamNetworkThread1 = streamNetworkThread(1, "stream network thread", server, stream_port)
        streamNetworkThread1.daemon = True
        streamNetworkThread1.start()
        while not listening:
            time.sleep(1)
        
        while listening:
            time.sleep(0.5)
    except Exception as e:
        traceback.print_exc()
    finally:
        print("Done")

if __name__ == "__main__":
    main()
