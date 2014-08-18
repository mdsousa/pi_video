import socket
import threading
import queue
import signal
import serial
import pynmea2
import datetime
import time
import sys
import traceback
import errno

server_ip = '10.42.0.1'
server_port = 5011
notClose = True

def signal_handler(signal, frame):
    global notClose
    print("\ngps_read::Ctrl-C pressed")
    notClose = False
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

def sendGPSData(serial, queue):
#    print("serial: %s" % serial)
    soc = queue.get()
    count = 1
    while True:
        try:
#    print('s: %s' % s)
            msg = serial.readline().decode()
            if( count%150 == 0 ):
                print('gps msg: %s' % msg)
            count += 1
            nmea_msg = pynmea2.parse(msg)
#            print("%s\n" % nmea_msg)
#    nmea_msg = pynmea2.parse(s.readline().decode())
#    nmea_msg = pynmea2.parse(s.readline().decode())
#            print('nmea_msg: %s' % nmea_msg)
#    print('nmea_msg.sentence_type: %s' % nmea_msg.sentence_type)
            if nmea_msg.sentence_type == "RMC":
#                print("%s\n" %nmea_msg)
#                print('Latitude: %d, %s' % (nmea_msg.latitude, nmea_msg.lat_dir))
                # print('Longitude: %d, %s' % (nmea_msg.longitude, nmea_msg.lon_dir))
                # print('GPS Heading: %d' % nmea_msg.true_course)
                # print('Date/Time: %s\n' % datetime.datetime.combine(nmea_msg.datestamp, nmea_msg.timestamp).isoformat())
                soc.sendall(msg.encode())
#                soc.send(nmea_msg.encode('utf-8'))
                time.sleep(0.1)
            else:
                print('wrong msg: %s' % nmea_msg)
        except pynmea2.nmea.ChecksumError as ce:
#            print("ChecksumError: %s" % ce)
            pass
        except pynmea2.nmea.ParseError as pe:
#            print("ParseError: %s" % pe)
            pass
        except UnicodeDecodeError as ud:
            print("UnicodeDecodeError: %s" % ud)
            pass
        except AttributeError as ae:
#            print("AttributeError: %s" % ae)
            pass
        except ValueError as ve:
            print("ValueError: %s" % ve)
            pass
        except TypeError as te:
            print("TypeError: %s" % te)
            pass
        except:
            traceback.print_exc(file=sys.stdout)
            print("closing serial port")
            soc.close()
            serial.close()
            break
#        finally:

def openSocket(ip, port, q):
    global notClose
    while notClose:
        try:
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#            soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#            print("ip: %s, port: %d" % (ip, port))
            soc.connect( (ip, port) )
            q.put(soc)
#            return soc
            break
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
#                print("Connection refused")
                pass
            else:
                traceback.print_exc(file=sys.stdout)

def main():
    try:
        s = serial.Serial("/dev/ttyAMA0", 57600)
#        print("s: %s" % s)

        soc_queue = queue.Queue(1)
        # msg = s.readline().decode()
        # nmea_msg = pynmea2.parse(msg)
        # print('nmea_msg: %s' % nmea_msg)

#        sock = openSocket(server_ip, server_port, soc_queue)
        t1 = threading.Thread(target=openSocket, args=(server_ip, server_port, soc_queue))
        t1.daemon = True
        t1.start()
#        print("sock: %s" % sock)
        t2 = threading.Thread(target=sendGPSData, args=(s,soc_queue))
#        print("t1: %s" % t1)
        t2.daemon = True
        t2.start()
        while True:
            time.sleep(0.01)
    except:
        print("Exception in main()")
        traceback.print_exc(file=sys.stdout)
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
