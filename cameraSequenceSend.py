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
cmd_client_socket1 = None
cmd_port1 = None # listen for commands from server
stream_client_socket1 = None
stream_connection1 = None
stream_port1 = None # send image stream to server
cmd_client_socket2 = None
cmd_port2 = None
stream_client_socket2 = None
stream_connection2 = None
stream_port2 = None

stream_write_length = None # how long stream should be saved to disk, in seconds

listening = False # set to True when connection is established
listenForCmdThread = None

doneSending = False

def signal_handler(signal, frame):
    print("\nCtrl-C pressed")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def readConfig():
    global server
    global cmd_port1
    global stream_port1
    global stream_write_length
    try:
        parser = configparser.ConfigParser()
        parser.read('pi_config.ini')
        server = parser['configuration']['server']
        cmd_port1 = int(parser['configuration']['cmd_port1'])
#        print("listen_port: %s" % listen_port)
        stream_port1 = int(parser['configuration']['stream_port1'])
        stream_write_length = int(parser['camera']['stream_write_length'])
    except configparser.Error as e:
        print(e)
#print(config['configuration'])

def cleanup():
    # global cmd_client_socket1
    # global cmd_client_socket2
    global stream_client_socket1
    global stream_client_socket2
    global stream_connection1
    global stream_connection2
    global listening
    global doneSending
    doneSending = True
#        stream_connection1.close()
#        stream_client_socket1.shutdown(socket.SHUT_RDWR)
#        stream_client_socket1.close()
#        stream_client_socket1 = None
    if(stream_client_socket1 is not None):
        stream_client_socket1.shutdown(socket.SHUT_RDWR)
        stream_client_socket1.close()
    time.sleep(0.5)
    listening = False
    print("cleaned up")


class listenForCmd(threading.Thread):
    def __init__(self, threadID, name, socket_arg):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.socket = socket_arg

    def run(self):
        global listening
        global cmd_client_socket1
#        print("Listening for cmds on socket: %s" % cmd_client_socket1)
        try:
#            cmd_client_socket1.listen(0) 
            listening = True
            while listening:
#                msg = cmd_client_socket1.recv(16).decode('utf-8')
                msg = self.socket.recv(16).decode('utf-8')
                print(msg)
                if msg == "r":
                    print('record command received')
                elif msg == "s":
                    print('save command received')
                elif msg == "e":
                    cleanup()
                    listening = False
#                    print('e received, exiting')
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except:
            traceback.print_exc(file=sys.stdout)


class listenNetworkThread(threading.Thread):
    def __init__(self, threadID, name, server, lport):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.server = server
        self.cmd_port = lport
        self.cmd_client_socket = None
    def run(self):
        global listeForCmdThread
        global cmd_client_socket
        while True:
#            print("attempt to listen to ip: %s, port: %d" % (self.server, self.cmd_port1))
            try:
#                cmd_client_socket1 = socket.socket()
#                cmd_client_socket1.connect( (self.server, self.cmd_port) )
                self.cmd_client_socket = socket.socket()
                self.cmd_client_socket.connect( (self.server, self.cmd_port) )
#                listenForCmdThread = listenForCmd(1, "listen for cmds", cmd_client_socket)
                listenForCmdThread = listenForCmd(1, "listen for cmds", self.cmd_client_socket)
                listenForCmdThread.daemon = True
                listenForCmdThread.start()
#                print('server: %s, port %d connected' % (self.server, self.cmd_port))
#                time.sleep(0.5) # give thread time to breath
                break
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
#                    print('connection error: %s' % e)
                    pass

# Prepare to send image data to remote server
class streamNetworkThread(threading.Thread):
#    global server
#    global stream_port1
    def __init__(self, threadID, name, server, sport):
        threading.Thread.__init__(self)
        print("streamNetworkThreade init")
        self.threadID = threadID
        self.server = server
        self.stream_port = sport
        self.stream_conn = None

    def run(self):
        # global stream_client_socket1
        # global stream_connection1
        print("streamNetworkThread run")
        while True:
            try:
#                stream_client_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # stream_client_socket1 = socket.socket()
                # stream_client_socket1.connect( (self.server, self.stream_port) )
                stream_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                stream_client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                stream_client_socket.connect( (self.server, self.stream_port) )
#                stream_connection1 = stream_client_socket1.makefile('wb')
#                stream_conn = stream_client_socket1.makefile('wb')
                self.stream_conn = stream_client_socket.makefile('wb')
                print("connected to server %s, %d" % (self.server, self.stream_port))
                s1 = threading.Thread(target=imageStreaming, args=(self.stream_conn,))
                s1.daemon = True
                s1.start()
                break
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    pass
                elif e.errno == ECONNRESET:
                    print("streamNetworkThread, seems the server has hung up.")
                else:
                    print("streaming connection exception")
                    traceback.print_exc(file=sys.stdout)

def imageStreaming(sconnection):
#    global stream_connection1
    global doneSending
    try:
        #        stream_connection = stream_socket.makefile('wb')
#        print("imageStreaming")
        with picamera.PiCamera() as camera:
            print("starting preview")
            # Start a preview and let the camera warm up for 2 seconds
            camera.start_preview()
            time.sleep(2)

            # Note the start time and construct a stream to hold image data
            # temporarily (we could write it directly to connection but in this
            # case we want to find out the size of each capture first to keep
            # our protocol simple)
            start = time.time()
            cameraStream = io.BytesIO()
            camera.resolution = (1920,1080) # HD
            for foo in camera.capture_continuous(cameraStream, format='jpeg', use_video_port=True):
                if( not doneSending ):
                    # Write the length of the capture to the stream and flush to
                    # ensure it actually gets sent
                    sconnection.write(struct.pack('<L', cameraStream.tell()))
                    sconnection.flush()
                    # Rewind the stream and send the image data over the wire
                    cameraStream.seek(0)
                    sconnection.write(cameraStream.read())
                    # If we've been capturing for more than 30 seconds, quit
                    if time.time() - start > 30:
                        break
                    # Reset the stream for the next capture
                    cameraStream.seek(0)
                    cameraStream.truncate()
                    # Write a length of zero to the stream to signal we're done
                else:
                    break
            print("Done sending!")
            sconnection.write(struct.pack('<L', 0))
            camera.close()
    except picamera.PiCameraError as e:
        print("imageStreaming PiCameraError: %s " % e)
        traceback.print_exc(file=sys.stdout)
    except IOError as ioe:
        if ioe.errno == errno.ECONNRESET:
            print("imageStreaming, seems the server has hung up.")
        else:
            print("imageStreaming IOError: %s" % ioe)
            traceback.print_exc(file=sys.stdout)
    finally:
        if(sconnection is not None):
            print("closing sconnection: %s" % sconnection)
            sconnection.close()

def main():
    global server
    global cmd_port1
    global cmd_port2
    global stream_port1
    global stream_port2
    global listenForCmdThread
#    anyInterface = '0.0.0.0'
    try:
        readConfig()
        streamNetworkThread1 = streamNetworkThread(1, "stream network thread", server, stream_port1)
        streamNetworkThread1.daemon = True
        streamNetworkThread1.start()
        listenNetworkThread1 = listenNetworkThread(1, "listen network thread2", server, cmd_port1)
        listenNetworkThread1.daemon = True
        listenNetworkThread1.start()
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
