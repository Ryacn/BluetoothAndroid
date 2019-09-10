import os
import glob
import time
from bluetooth import *
from picamera import PiCamera
import time
# import multiprocessing
# from multiprocessing import Process
from threading import Thread
import select

def getFilesInfo():
    main_dir = '/home/pi/AndroidPi/Camera/'
    file_list = glob.glob(main_dir + '*')
    ret_string = ''
    for file_dir in file_list:
        ret_string += os.path.basename(file_dir) + ' ' + str(os.path.getsize(file_dir)) + ','
    return ret_string[:-1]

_FINISH = True
def runCamera():
    global _FINISH
    if _FINISH:
        _FINISH = False
        try:
            with PiCamera() as camera:
                print("preparing camera")
                time.sleep(2)
                camera.capture('/home/pi/AndroidPi/Camera/' + str(time.time()) + '.jpg')
                _FINISH = True
                print("picture taken")
        except:
            print 'camera process error'
            _FINISH = True
        
def sendFile(filename, conn):
    main_dir = '/home/pi/AndroidPi/Camera/'
    if os.path.exists(main_dir + os.path.basename(filename)):
        with open(main_dir + os.path.basename(filename), 'rb') as f:
            line = f.read(1024)
            print("Beginning file transfer")
            test = 0
            while line:
                test += len(line)
                conn.sendall(line)
                line = f.read(1024)
            print('transfer complete')
            print 'sending...' + str(test) + ' bytes'
    else:
        print 'requrested file that does not exist'

server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service( server_sock, "AquaPiServer",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ], 
#                   protocols = [ OBEX_UUID ] 
                    )

end_string_indicator = '!'
p1 = None
while True:          
    print "Waiting for connection on RFCOMM channel %d" % port

    client_sock, client_info = server_sock.accept()
    print "Accepted connection from ", client_info

    try:
        data = client_sock.recv(1024)
        if len(data) == 0: break
        print "received [%s]" % data

        if data == 'get_files_dir':
            data = getFilesInfo() + end_string_indicator
            client_sock.send(data)
            print "sending [%s]" % data
        elif data == 'take_picture':
            if _FINISH:
                data = 'camera_request_accepted' + end_string_indicator
                p1 = Thread(target=runCamera)
                p1.start()
            else:
                data = 'camera_request_rejected' + end_string_indicator
            client_sock.send(data)
            print "sending [%s]" % data
        else:
            sendFile(data, client_sock)
            print "sending file [%s]" % data

    except IOError:
        pass

    except KeyboardInterrupt:

        print "disconnected"

        client_sock.close()
        server_sock.close()
        print "all done"

        break