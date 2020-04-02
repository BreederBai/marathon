#! /usr/bin/env python
"""\
Read data from serial ports and send to remote server.

Design by maben (C) 2013.09.26 

"""

import serial
import time
import re
import json
import ConfigParser
import os
import struct
import socket
import threading


class Main:
    __cfg = {
            'hardware' : {},
            'send' : {},
            'recv' : {},
            'log' : {}
        }
    __serial = None
    __mac = None
    __address = None
    __socket = None

    def __init__(self):
        self.__loadConfig()
        self.__initSerialPort()
        self.__mac = self.__getMAC()
        
        self.__address = (self.__cfg['send']['remoteIp'], self.__cfg['send']['remotePort'])
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def __loadConfig(self):
        proDir = os.path.split(os.path.realpath(__file__))[0]
        configPath = os.path.join(proDir, "config.txt")
        path = os.path.abspath(configPath)
        #print(configPath)
        #print(path)

        cfg = ConfigParser.ConfigParser()
        try:
            cfg.read(path)
            self.__cfg['hardware']['serialDev'] = cfg.get('HARDWARE','SERIAL_DEV')
            self.__cfg['hardware']['baudrate'] = cfg.get('HARDWARE','BAUDRATE')
            self.__cfg['send']['remoteIp'] = cfg.get('SEND','REMOTE_IP')
            self.__cfg['send']['remotePort'] = int(cfg.get('SEND','REMOTE_PORT'))
            self.__cfg['send']['delay'] = float(cfg.get('SEND','DELAY'))
            self.__cfg['recv']['delay'] = float(cfg.get('RECV','DELAY'))
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
        self.__serial.timeout = 2
        try:
            if not self.__serial.isOpen():
                self.__serial.open()
        except:
            self.__halt('Cannot open serial port!')
        finally:
            pass

    def __readSerialData(self):
        #self.__serial.flushOutput()
        #self.__serial.flushInput()
        n = self.__serial.inWaiting()
        
        s = None
        if n:
            s = self.__serial.read(n)
            #print type(s),len(s)
        return s

    def __sendSerialData(self,data):
        self.__serial.write(data)

    def __sendData(self,data):
        try:
            #data['data'] = "\xAAU\x00sdwqadwdaw"
            #params = urllib.urlencode(data)
            #print len(params)
            #print data
            #print params
            #request = urllib2.Request(self.__cfg['send']['remoteUrl'],params)
            #response = urllib2.urlopen(request)

            self.__socket.sendto(data,self.__address)
        except:
            self.__writeLog('Send data to server failed')
        finally:
            pass

    def __recvDataUdp(self):
        data = None
        try:
            data = self.__socket.recv(255)
        except:
            self.__writeLog('Send data to server failed')
        finally:
            pass

        return data

        

    def __getMAC(self):
        process = os.popen('/sbin/ifconfig wlp4s0')
        info = process.read()
        process.close()
        mac = re.search("HWaddr\s+(\S+)",info)
        if mac:
            return mac.group(1)
        else:
            return '00-00-00-00-00-00'

    def loop1(self):
        print ('loop1 start')
        step = 0
        data = {}
        while True:
            data = self.__readSerialData()
            if data != None:
                self.__sendData(data)
                time.sleep(self.__cfg['send']['delay'])
                #print ('loop1:I am alive %d' %len(data))
                step = step + 1
            else:
                #print ('loop1: data is None')
                time.sleep(self.__cfg['send']['delay'])

    def loop2(self):
        print ('loop2 start')
        step = 0
        while True:
            data = self.__recvDataUdp()
            if data != None:
                self.__sendSerialData(data)
                time.sleep(self.__cfg['recv']['delay'])
                #print ('loop2:I am alive %d' %len(data))
                #print('__recvDataUdp:%s' %data)

                #for index in range(len(data)):
                #    print('',data[index])
                
                #print('**********')
                step = step + 1
            else:
                #print ('loop2: data is None')
                time.sleep(self.__cfg['recv']['delay'])

    def run(self):
        t1 = threading.Thread(target=self.loop1, name='LoopThreadUpward')
        t2 = threading.Thread(target=self.loop2, name='LoopThreadDown')
        t1.start()
        t2.start()
        t1.join()
        t2.join()

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
