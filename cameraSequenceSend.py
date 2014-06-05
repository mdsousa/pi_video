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

stream_write_length = None # how long stream should be saved to disk, in seconds

listening = False # set to True when connection is established
listenForCmdThread = None


def signal_handler(signal, frame):
    print("\nCtrl-C pressed")
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def cleanup():
    global cmd_client_socket1
    global stream_client_socket1
    global stream_connection1
    global listening
    if(cmd_client_socket1 is not None):
        cmd_client_socket1.close()
    if stream_connection1 is not None and stream_connection1.closed != False:
        stream_connection1.close()
        stream_client_socket1.shutdown(socket.SHUT_RDWR)
        stream_client_socket1.close()
        stream_client_socket1 = None
    if(stream_client_socket1 is not None):
        stream_client_socket1.shutdown(socket.SHUT_RDWR)
        stream_client_socket1.close()
    listening = False
    print("cleaned up")

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


class listenForCmd(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID

    def run(self):
        global listening
        global cmd_client_socket1
#        print("Listening for cmds on socket: %s" % cmd_client_socket1)
        try:
#            cmd_client_socket1.listen(0) 
            listening = True
            while listening:
                msg = cmd_client_socket1.recv(16).decode('utf-8')
                print(msg)
                if msg == "r":
                    print('record command received')
                elif msg == "s":
                    print('save command received')
                elif msg == "e":
                    cleanup()
#                    listening = False
                    print('e received, exiting')
        except:
            traceback.print_exc(file=sys.stdout)


class listenNetworkThread(threading.Thread):
    def __init__(self, threadID, name, server, lport):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.server = server
        self.cmd_port1 = lport
    def run(self):
        global listeForCmdThread
        global cmd_client_socket1
        while True:
#            print("attempt to listen to ip: %s, port: %d" % (self.server, self.cmd_port1))
            try:
                cmd_client_socket1 = socket.socket()
                cmd_client_socket1.connect( (self.server, self.cmd_port1) )
                listenForCmdThread = listenForCmd(1, "listen for cmds")
                listenForCmdThread.daemon = True
                listenForCmdThread.start()
#                print('server: %s, port %d connected' % (self.server, self.cmd_port1))
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
        self.stream_port1 = sport

    def run(self):
        global stream_client_socket1
        global stream_connection1
        print("streamNetworkThread run")
        while True:
            try:
#                stream_client_socket1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                stream_client_socket1 = socket.socket()
                stream_client_socket1.connect( (self.server, self.stream_port1) )
                stream_connection1 = stream_client_socket1.makefile('wb')
                print("connected to server %s, %d" % (self.server, self.stream_port1))
                s1 = threading.Thread(target=imageStreaming)
                s1.daemon = True
                s1.start()
                break
            except socket.error as e:
                if e.errno == errno.ECONNREFUSED:
                    pass
                else:
                    print("streaming connection exception")
                    traceback.print_exc(file=sys.stdout)

#     def imageStreaming():
#         print("imageStreaming")
#         try:
#         #        stream_connection = stream_socket.makefile('wb')
#             print("1")
# #        print("imageStreaming")
#             with picamera.PiCamera() as camera:
#                 print("starting preview")
#             # Start a preview and let the camera warm up for 2 seconds
#                 camera.start_preview()
#                 time.sleep(2)

#             # Note the start time and construct a stream to hold image data
#             # temporarily (we could write it directly to connection but in this
#             # case we want to find out the size of each capture first to keep
#             # our protocol simple)
#                 start = time.time()
#                 stream = io.BytesIO()
#                 camera.resolution = (1920,1080) # HD
#                 for foo in camera.capture_continuous(stream, format='jpeg', use_video_port=True):
#                     # Write the length of the capture to the stream and flush to
#                     # ensure it actually gets sent
#                     self.stream_connection.write(struct.pack('<L', stream.tell()))
#                     self.stream_connection.flush()
#                     print("2")
#                     # Rewind the stream and send the image data over the wire
#                     stream.seek(0)
#                     print("3")
#                     self.stream_connection.write(stream.read())
#                     # If we've been capturing for more than 30 seconds, quit
#                     if time.time() - start > 30:
#                         break
#                     # Reset the stream for the next capture
#                     stream.seek(0)
#                     stream.truncate()
#                 # Write a length of zero to the stream to signal we're done
#                 self.stream_connection.write(struct.pack('<L', 0))
#                 camera.close()
#         except picamera.PiCameraError as e:
#             print("imageStreaming error: %s " % e)
#             traceback.print_exc(file=sys.stdout)
#         finally:
#             self.stream_connection.close()

def imageStreaming():
    global stream_connection1
    print("imageStreaming")
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
                # Write the length of the capture to the stream and flush to
                # ensure it actually gets sent
                stream_connection1.write(struct.pack('<L', cameraStream.tell()))
                stream_connection1.flush()
                # Rewind the stream and send the image data over the wire
                cameraStream.seek(0)
                stream_connection1.write(cameraStream.read())
                # If we've been capturing for more than 30 seconds, quit
                if time.time() - start > 30:
                    break
                # Reset the stream for the next capture
                cameraStream.seek(0)
                cameraStream.truncate()
                # Write a length of zero to the stream to signal we're done
            stream_connection1.write(struct.pack('<L', 0))
            camera.close()
    except picamera.PiCameraError as e:
        print("imageStreaming PiCameraError: %s " % e)
        traceback.print_exc(file=sys.stdout)
    except IOError as ioe:
        print("imageStreaming IOError: %s" % ioe)
        traceback.print_exc(file=sys.stdout)
    # finally:
    #     if( stream_connection1 is not None):
    #         stream_connection1.close()

def sendStream():
    global server
    global stream_port1
    def __init__(self, threadID, name, server, sport):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.server = server
        self.stream_port1 = sport
    def run(self):
        while True:
            try:
                print("streaming")
            except:
                pass


def main():
    global server
    global cmd_port1
    global stream_port1
    global listenForCmdThread
#    anyInterface = '0.0.0.0'
    try:
        readConfig()
        streamNetworkThread1 = streamNetworkThread(1, "stream network thread", server, stream_port1)
        streamNetworkThread1.daemon = True
        streamNetworkThread1.start()
        listenNetworkThread1 = listenNetworkThread(1, "listen network thread", server, cmd_port1)
#        listenNetworkThread1 = listenNetworkThread(1, "listen network thread", anyInterface, cmd_port1)
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
