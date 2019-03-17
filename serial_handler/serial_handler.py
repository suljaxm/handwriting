#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author:Created by GJ on 2018/6/6
@file:serial_manager.py
@desc:
'''
import serial.tools.list_ports
import serial
import threading
import binascii


class SerialHandler(object):
    # 串口对象
    ser = serial.Serial()

    def __init__(self):
        self.ser.port = None
        self.ser.baudrate = 9600
        self.ser.bytesize = 8
        self.ser.stopbits = 1
        self.ser.parity = serial.PARITY_NONE
        self.Com_List = []

        # 检测端口并获取从机串口
        self.ser.port = self.port_cheak()
        # 打开从机串口
        # self.port_open()

    def port_cheak(self):

        port_list = list(serial.tools.list_ports.comports())
        for port in port_list:
            s = serial.Serial(port=port[0], timeout=0.1)
            if s.read() == b'\x00':
                s.close()
                print(port[0])
                return port[0]
            s.close()
        return None

    def port_open(self):

        # name:设备名字
        # portstr:已废弃，用name代替
        # port：读或者写端口
        # baudrate：波特率
        # bytesize：字节大小
        # parity：校验位
        # stopbits：停止位
        # timeout：读超时设置
        # writeTimeout：写超时
        # xonxoff：软件流控
        # rtscts：硬件流控
        # dsrdtr：硬件流控
        # interCharTimeout:字符间隔超时
        if self.ser.port != None:
            self.ser.open()
            if (self.ser.isOpen()):
                print("打开成功")
            else:
                print("打开失败")

    def receive_data(self):
        print("The receive_data threading is start")
        res_data = ''
        num = 0
        while (self.ser.isOpen()):
            size = self.ser.inWaiting()  # 获取输入缓冲区中的字节数
            if size:
                res_data = self.ser.read_all()
                res_data_new = binascii.b2a_hex(res_data).decode()
                print('接收到的数据：%s' % (res_data_new))
                print(type(res_data_new))
                print(res_data_new[4:6])
                # binascii.b2a_hex(res_data).decode()

                self.ser.flushInput()
                num += 1
                print("接收：" + str(num))


if __name__ == '__main__':
    s = SerialHandler()
    s.port_open()
