#! /usr/bin/env python
"""\
Read data from serial ports and send to remote server.

Design by maben (C) 2013.09.26 

"""

import serial
import time
import re
import json
import urllib
import urllib2
import ConfigParser
import os
import struct

class Main:
    __cfg = {
            'hardware' : {},
            'send' : {},
            'recv' : {},
            'log' : {}
        }
    __serial = None
    __mac = None

    def __init__(self):
        self.__loadConfig()
        self.__initSerialPort()
        self.__mac = self.__getMAC()


    def __loadConfig(self):
        cfg = ConfigParser.ConfigParser()
        try:
            cfg.read('config.ini')
            self.__cfg['hardware']['serialDev'] = cfg.get('HARDWARE','SERIAL_DEV')
            self.__cfg['hardware']['baudrate'] = cfg.get('HARDWARE','BAUDRATE')
            self.__cfg['send']['remoteUrl'] = cfg.get('SEND','REMOTE_URL')
            self.__cfg['send']['delay'] = int(cfg.get('SEND','DELAY'))
            self.__cfg['recv']['remoteUrl'] = cfg.get('RECV','REMOTE_URL')
            self.__cfg['recv']['delay'] = int(cfg.get('RECV','DELAY'))
            self.__cfg['log']['enable'] = cfg.get('LOG','ENABLE')
            if self.__cfg['log']['enable'] == '1':
                self.__cfg['log']['path'] = cfg.get('LOG','PATH')

            for value in self.__cfg.values():
                for k,v in value.items():
                    if v == None:
                        self.__halt('All configuration items cannot be empty!')
        except:
            self.__halt('Load config failed')
        finally:
            pass

    def __initSerialPort(self):
        self.__writeLog('Initializing the serial port')
        self.__serial = serial.Serial(self.__cfg['hardware']['serialDev'],self.__cfg['hardware']['baudrate'])
        try:
            if not self.__serial.isOpen():
                self.__serial.open()
        except:
            self.__halt('Cannot open serial port!')
        finally:
            pass

    def __readSerialData(self):
        self.__serial.flushOutput()
        self.__serial.flushInput()
        s = self.__serial.read(150)
        #print type(s),len(s)
        return s

    def __sendData(self,data={}):
        try:
            #data['data'] = "\xAAU\x00sdwqadwdaw"
            params = urllib.urlencode(data)
            #print len(params)
            #print data
            #print params
            request = urllib2.Request(self.__cfg['send']['remoteUrl'],params)
            response = urllib2.urlopen(request)
        except:
            self.__writeLog('Send data to server failed')
        finally:
            pass

    def __getMAC(self):
        process = os.popen('/sbin/ifconfig wlp4s0')
        info = process.read()
        process.close()
        mac = re.search("HWaddr\s+(\S+)",info)
        if mac:
            return mac.group(1)
        else:
            return '00-00-00-00-00-00'

    def run(self):
        print ('run() start')
        data = {}
        #data['mac'] = self.__mac;
        while True:
            data['data'] = self.__readSerialData()
            self.__sendData(data)
            time.sleep(self.__cfg['send']['delay'])
            print ('I am alive')

    def __writeLog(self,log):
        if self.__cfg['log']['enable'] == '1':
            fp = open(self.__cfg['log']['path'],'a+')
            try:
                written = time.strftime('[%Y-%m-%d %H:%M:%S] ',time.localtime(time.time()))+log+"\r\n"
                fp.write(written)
            except:
                print ('Cannot written the log infomation')
            finally:
                fp.close()
                pass
        else:
            print ('log not enable')
            pass

    def __halt(self,msg,isWriteLog = True):
        if isWriteLog:
            self.__writeLog(msg)
        print (msg)
        exit()

    def __del__(self):
        if self.__serial and self.__serial.isOpen():
            self.__serial.close()

if  __name__ == '__main__':
    main = Main()
    main.run()
