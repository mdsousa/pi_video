import socket   #for sockets

import io
import time
import picamera
import struct

host = '10.42.0.1'
port = 5001
 
#Connect to remote server
client_socket = socket.socket()
client_socket.connect((host , port))
connection = client_socket.makefile('wb')

try:
    with picamera.PiCamera() as camera:
#        camera.resolution = (640, 480)
        camera.resolution = (1920,1080) # HD
        # Start a preview and let the camera warm up for 2 seconds
        camera.start_preview()
        time.sleep(2)

        camera.start_recording(connection, format='h264')
        camera.wait_recording(30)
        camera.stop_recording()

        # Note the start time and construct a stream to hold image data
        # temporarily (we could write it directly to connection but in this
        # case we want to find out the size of each capture first to keep
        # our protocol simple)
#        start = time.time()
#        stream = io.BytesIO()
#        for foo in camera.capture_continuous(stream, format='jpeg'):
            # Write the length of the capture to the stream and flush to
            # ensure it actually gets sent
#            connection.write(struct.pack('<L', stream.tell()))
#            connection.flush()
#            # Rewind the stream and send the image data over the wire
#            stream.seek(0)
#            connection.write(stream.read())
            # If we've been capturing for more than 30 seconds, quit
#            if time.time() - start > 30:
#                break
            # Reset the stream for the next capture
#            stream.seek(0)
#            stream.truncate()
    # Write a length of zero to the stream to signal we're done
#    connection.write(struct.pack('<L', 0))
#    camera.close()
finally:
    connection.close()
    client_socket.close()
