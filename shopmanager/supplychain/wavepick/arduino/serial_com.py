import urllib
import serial
import time
import json
import random

def requstAndWrite(url, ser):
    con = urllib.urlopen(url)
    msg = con.read()
    n = ser.write(msg)

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyACM0', 9600)
    print ser.portstr

    url = "http://m.xiaolumeimei.com/supplychain/wavepick/publish/1/"
    ser.open()
    
    requstAndWrite(url,ser)
    while True:
        r = ser.read()
        if r == 'r':
            requstAndWrite(url,ser)

    ser.close()
