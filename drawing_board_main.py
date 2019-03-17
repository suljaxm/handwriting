# -*- coding: utf-8 -*-
import binascii
import logging
import multiprocessing
import os
import sys
import threading
import time

from PyQt5.QtCore import Qt, QDateTime, QPoint
from PyQt5.QtGui import QPainter, QPen, QPixmap, QIcon, QBrush, QPixmapCache
from PyQt5.QtWidgets import (QMainWindow, QApplication, QDesktopWidget,
                             QPushButton, QMenu, QFileDialog, QAction, QSystemTrayIcon, QMessageBox, qApp)

import g_hw_render
from Networks.apiRequest import HttpRequest
from Screenshots.screenshots import ScreenShotsWin
from serial_handler.serial_handler import SerialHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
ch = logging.StreamHandler()
formatter = logging.Formatter('%(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

is_share = False  # 设置分享线程的全局变量


class DrawingBoardUIBusi(QMainWindow):
    # 单例模式
    # _instance = None
    #
    # def __new__(cls, *args, **kw):
    #     if not cls._instance:
    #         cls._instance = super(DrawingBoardUIBusi, cls).__new__(cls, *args, **kw)
    #     return cls._instance

    def __init__(self, meetingId=None, meetingNumber=None):
        super(DrawingBoardUIBusi, self).__init__()

        self.meetingNumber = meetingNumber  # 会议编号
        self.meetingId = meetingId  # 会议号

        self.init_parameters()  # 初始化系统参数
        self.setupUi()  # 创建UI
        self.setWindowOpacity(1)  # 设置透明度
        self.init_serial_port()  # 初始化串口通信

    def init_serial_port(self):
        # 初始化串口通信，接收命令
        self.serial = SerialHandler()

        if self.serial.ser.port != None:
            self.serial.port_open()
            self.t1 = threading.Thread(target=self.receive_data, daemon=True)
            # 多线程改为多进程
            # self.t1 = multiprocessing.Process(target=self.receive_data)
            # self.t1.setDaemon(True)
            self.t1.start()
            print('串口通信多进程开启')

    def receive_data(self):
        # 一直接收串口命令，执行相应的指令
        print("The receive_data threading is start")
        res_data = ''
        num = 0
        while (self.serial.ser.isOpen()):
            time.sleep(1)  # 查询不那么频繁
            size = self.serial.ser.inWaiting()  # 获取输入缓冲区中的字节数
            if size:
                res_data = self.serial.ser.read_all()
                res_data_new = binascii.b2a_hex(res_data).decode()
                print('接收到的数据：%s' % (res_data_new))
                print(res_data_new.find('01'))

                if res_data_new[4:6] == '01':
                    # 按键1--清屏
                    self.clearScree()
                elif res_data_new[4:6] == '02':
                    # 按键2--保存
                    self.savePicture(True)
                elif res_data_new[4:6] == '03':
                    # 按键3--上一页
                    print('上一页')
                    self.previousPage()
                elif res_data_new[4:6] == '04':
                    # 按键4--下一页
                    print('下一页')
                    self.nextPage()
                elif res_data_new[4:6] == '05':
                    # 按键5--黑笔
                    self.changeColor(0)
                elif res_data_new[4:6] == '06':
                    # 按键6--蓝笔
                    self.changeColor(1)
                elif res_data_new[4:6] == '07':
                    # 按键7--红笔
                    self.changeColor(2)
                elif res_data_new[4:6] == '08':
                    # 按键8--擦除
                    self.erase()

                # binascii.b2a_hex(res_data).decode()

                self.serial.ser.flushInput()  # 刷新输入缓冲区
                num += 1
                print("接收：" + str(num))

    def setupUi(self):
        '''
        创建UI,
        :return:
        '''

        self.setObjectName('drawWindow')  # 对象名
        self.setWindowTitle('白板')  # 设置标题
        self.resize(self.resolution.width(), self.resolution.height())
        self.setWindowIcon(QIcon("qrc\Icon.png"))  # 设置图标
        self.setWindowFlags(Qt.Tool | Qt.X11BypassWindowManagerHint)  # 任务栏隐藏图标
        # self.setWindowTitle('当前' + str(self.page) + '页')  # 标题显示第几页
        self.setWindowTitle('当前' + '页')  # 标题显示第几页
        # self.setWindowFlags(
        #     Qt.CustomizeWindowHint | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(self.width(), self.height())  # 设置主窗口禁止调整大小

        # 创建白板的功能键
        btn_names = ['清屏', '保存', '切换', '上一页', '下一页', '黑笔', '蓝笔', '红笔', '擦除', '功能', '恢复', '加载']

        # 各个按钮的位置
        positions = [(self.resolution.width() - self.resolution.height() / len(btn_names),
                      (y * self.resolution.height() / len(btn_names))) for y in range(0, len(btn_names))]

        # 每个功能按钮的高度
        height = (self.resolution.height() / len(btn_names)) * 0.98

        '''要重构这部分代码'''
        # 清屏
        self.btn_clean = QPushButton(btn_names[0], self)
        self.btn_clean.resize(height, height)
        self.btn_clean.move(positions[0][0], positions[0][1])
        self.btn_clean.clicked.connect(self.clearScree)
        self.btn_clean.setVisible(False)
        # self.btn_clean.setStyleSheet("background-color: rgba(0,125,0,0)")
        # 保存
        self.btn_savePicture = QPushButton(btn_names[1], self)
        self.btn_savePicture.resize(height, height)
        self.btn_savePicture.move(positions[1][0], positions[1][1])
        self.btn_savePicture.clicked.connect(lambda: self.savePicture(False))
        self.btn_savePicture.setVisible(False)

        # 切换
        self.btn_switch = QPushButton(btn_names[2], self)
        self.btn_switch.resize(height, height)
        self.btn_switch.move(positions[2][0], positions[2][1])
        self.btn_switch.clicked.connect(self.switch)
        self.btn_switch.setVisible(False)

        # 上一页
        self.btn_previousPage = QPushButton(btn_names[3], self)
        self.btn_previousPage.resize(height, height)
        self.btn_previousPage.move(positions[3][0], positions[3][1])
        self.btn_previousPage.clicked.connect(self.previousPage)
        self.btn_previousPage.setVisible(False)

        # 下一页
        self.btn_nextPage = QPushButton(btn_names[4], self)
        self.btn_nextPage.resize(height, height)
        self.btn_nextPage.move(positions[4][0], positions[4][1])
        self.btn_nextPage.clicked.connect(self.nextPage)
        self.btn_nextPage.setVisible(False)

        # 黑笔
        self.btn_changeColor1 = QPushButton(btn_names[5], self)
        self.btn_changeColor1.resize(height, height)
        self.btn_changeColor1.move(positions[5][0], positions[5][1])
        self.btn_changeColor1.clicked.connect(lambda: self.changeColor(0))
        self.btn_changeColor1.setEnabled(True)
        self.btn_changeColor1.setVisible(False)

        # 蓝笔
        self.btn_changeColor2 = QPushButton(btn_names[6], self)
        self.btn_changeColor2.resize(height, height)
        self.btn_changeColor2.move(positions[6][0], positions[6][1])
        self.btn_changeColor2.clicked.connect(lambda: self.changeColor(1))
        self.btn_changeColor2.setEnabled(True)
        self.btn_changeColor2.setVisible(False)

        # 红笔
        self.btn_changeColor3 = QPushButton(btn_names[7], self)
        self.btn_changeColor3.resize(height, height)
        self.btn_changeColor3.move(positions[7][0], positions[7][1])
        self.btn_changeColor3.clicked.connect(lambda: self.changeColor(2))
        self.btn_changeColor3.setEnabled(True)
        self.btn_changeColor3.setVisible(False)

        # 擦除
        self.btn_erase = QPushButton(btn_names[8], self)
        self.btn_erase.resize(height, height)
        self.btn_erase.move(positions[8][0], positions[8][1])
        self.btn_erase.clicked.connect(self.erase)
        self.btn_erase.setVisible(False)
        '''
        # 功能
        self.btn_startSharing = QPushButton(btn_names[9], self)
        self.btn_startSharing.resize(height, height)
        self.btn_startSharing.move(positions[9][0], positions[9][1])
        self.btn_startSharing.clicked.connect(self.startSharing)

        # 恢复
        self.btn_restorePicture = QPushButton(btn_names[10], self)
        self.btn_restorePicture.resize(height, height)
        self.btn_restorePicture.move(positions[10][0], positions[10][1])
        self.btn_restorePicture.clicked.connect(self.restorePicture)

        # 加载
        self.btn_loadPicture = QPushButton(btn_names[11], self)
        self.btn_loadPicture.resize(height, height)
        self.btn_loadPicture.move(positions[11][0], positions[11][1])
        self.btn_loadPicture.clicked.connect(self.loadPicture)
        '''

    def init_parameters(self):
        '''
        初始化系统参数,可读取系统配置文件
        :return:
        '''

        self.count = 0

        self.resolution = QDesktopWidget().availableGeometry()  # 获取显示器的分辨率-->(0, 0, 1366, 728)
        self.monitor = QDesktopWidget()  # 获得显示器的物理尺寸
        # self.setWindowFlags(Qt.Tool | Qt.X11BypassWindowManagerHint)  # 任务栏隐藏图标

        # 会议号
        self.meetingID = 0  # 当前会议号
        # 页数记录
        self.page = 1  # 当前所在页页码
        self.pages = 1  # 总页数
        self.isWritting = False  # 是否正在输入
        self.isWritten = False  # 记录当前页是否有新写入

        ##########2018-6-12 添加###########

        self.httpRequest = HttpRequest()  # http请求对象那
        self.is_login = True  # 用户是否登录

        # self.shareThread = threading.Thread(target=self.meetingConnection, daemon=True)  # 创建一个实时分享的线程
        # self.shareThread.start()
        # 多线程改为多进程
        self.shareThread = threading.Thread(target=self.self_check_net, daemon=True)  # 创建一个实时分享的线程
        self.shareThread.start()
        # print('# 创建一个实时分享的进程1')
        # self.shareProcess = multiprocessing.Process(target=self.self_check_net)  # 创建一个实时分享的进程
        # self.shareProcess.start()
        # print('# 创建一个实时分享的进程2')

        self.screenshotFullScreen = ScreenShotsWin()  # 用于截全屏的对象

        ##########2018-6-12 添加###########

        # 记录笔迹（坐标，颜色）
        self.penColor = 0  # 笔的初始颜色黑色
        self.pos_xyc = []  # [((x, y), c)]  c->0 1 2 3
        self.pos_pages = {}  # 存放所有页笔画路径{page : pos_xyc}

        # 设置不追踪鼠标
        self.setMouseTracking(False)

        # 使用指定的画笔，宽度，钢笔样式，帽子样式和连接样式构造笔
        self.pen = QPen(Qt.black, 4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        # 画布pix
        self.pix = QPixmap(self.resolution.size())
        self.pix.fill(Qt.white)

        self.pix = QPixmap(self.resolution.size())
        self.pix.fill(Qt.white)
        # self.pix.save('原图.png')

        # 黑板擦
        '''
            改用  eraseRect ，直接去掉笔画
            void QPainter::eraseRect(const QRectF &rectangle)
            Erases the area inside the given rectangle. Equivalent to calling
            fillRect(rectangle, background()).
        '''
        self.paintEase = QPainter(self)
        self.paintEase.setPen(QPen(Qt.black, Qt.DashLine))
        self.paintEase.setBrush(QBrush(Qt.red, Qt.SolidPattern))

        # 是否擦除
        self.eraseable = False

        # 起点终点
        self.lastPoint = QPoint()
        self.endPoint = QPoint()

        self.icon = QIcon("icon\Icon.png")  # 窗体图标
        self.addSystemTray()  # 设置系统托盘

    def addSystemTray(self):
        '''
        系统托盘，显示、隐藏主窗体，退出程序
        :return:
        '''
        minimizeAction = QAction("隐藏", self, triggered=self.hide)  # 隐藏菜单
        maximizeAction = QAction("显示", self, triggered=self.show)  # 显示菜单
        restoreAction = QAction("恢复", self, triggered=self.showNormal)  # 恢复菜单
        quitAction = QAction("退出", self, triggered=self.close)  # 退出菜单
        self.trayIconMenu = QMenu(self)
        self.trayIconMenu.addAction(minimizeAction)
        self.trayIconMenu.addAction(maximizeAction)
        self.trayIconMenu.addAction(restoreAction)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(quitAction)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(self.icon)  # 设置系统托盘图标
        self.setWindowIcon(self.icon)  # 设置系统窗体图标
        self.trayIcon.setContextMenu(self.trayIconMenu)  # 添加右键菜单
        self.trayIcon.activated.connect(self.trayClick)  # 左键点击托盘

        self.trayIcon.show()

    def trayClick(self, event):
        '''
        双击系统托盘显示主窗体
        :param event:
        :return:
        '''
        if event == QSystemTrayIcon.DoubleClick:  # 双击
            self.showNormal()
        else:
            pass

    def applyForMeetingNum(self):
        '''
        申请会议号
        :return:
        '''
        response = self.httpRequest.applyForMeetingNum()
        # result = json.loads(response.content)
        try:
            result = response.json()['data']
            print(type(result))
            logger.debug(result)
            self.meetingId, self.meetingNumber = result.split('&')  # 截取会议编号
            logger.debug(self.meetingId)
            logger.debug(self.meetingNumber)
            QMessageBox.information(self, '申请会议号成功', '会议号：' + self.meetingNumber, QMessageBox.Ok)
        except:
            logger.debug('网络衔接失败')
            QMessageBox.warning(self, '警告', '网络连接失败！请检查网络设备！', QMessageBox.Cancel)

    def meetingConnection(self):
        logger.debug('查询用户请求')
        while (True):
            if self.is_login and is_share:
                time.sleep(2)  # 等待1s
                logger.debug('分享开启')
                try:
                    response = self.httpRequest.meetingConnection(self.meetingId)
                    result = response.json()
                    code = result['code']
                    print(result, code)
                    if code == '0':
                        # 需再次建立会议连接
                        print('需再次建立会议连接')
                        time.sleep(2)  # 等待1s
                        continue
                    elif code == '1':
                        # 有用户需要截屏
                        print('有用户需要截屏')
                        t_upload = threading.Thread(target=self.uploadPic, daemon=True)
                        t_upload.start()
                        t_upload.join()
                        time.sleep(5)  # 等待1s
                    elif code == '-1':
                        # 请求过于频繁，当前已有连接处于等待状态
                        print('请求过于频繁，当前已有连接处于等待状态')
                        time.sleep(5)  # 等待1s
                        continue
                    else:
                        print('“会议不存在，请重新分配会议号”')
                except:
                    logger.debug('网络衔接失败')
            else:
                # logger.debug('分享关闭')
                pass

    def self_check_net(self):
        print('分享线程开始')
        while (True):
            print('循環')
            flag = self.count == 0
            time.sleep(2)
            if flag:
                if self.count == 0:
                    self.weather_con()

    def weather_con(self):
        print('+++++ 查询服务器请求 ++++++')
        if self.is_login and is_share and self.count <= 2:
            self.count += 1
            response = self.httpRequest.meetingConnection(self.meetingId)
            print('response: %s' % response)
            if response != None:
                result = response.json()
                print(result)
                code = result['code']
                self.count -= 1
                print('result:', result)
                if code == '0':
                    print('code: 0')
                    self.weather_con()
                elif code == '1':
                    print('code: 1')
                    # t_upload = threading.Thread(target=self.uploadPic, daemon=True)
                    # t_upload.start()
                    print('截图多进程1')
                    p_upload = multiprocessing.Process(target=self.uploadPic)
                    p_upload.start()
                    print('截图多进程1')

                    # self.weather_con()
                elif code == '-1':
                    print('code: -1')
                    pass
                elif code == '-2':
                    print('code: -2')
                    self.applyForMeetingNum()

    def uploadPic(self):
        self.screenshotsFullScreen()  # 截图

        fileName = 'save/temp/' + str(self.page) + '.jpg'

        files = {
            'file': open(fileName, 'rb')
        }
        print('开始上传图片')
        respone = self.httpRequest.uploadPic(files=files, meetingId=self.meetingId, pageNum=self.page)

        print('上传图片成功')
        print(respone)

    def screenshotsFullScreen(self):
        '''
        截图全图
        :return:全屏的截图pix.png
        '''
        pix = self.screenshotFullScreen.screenshotsFullScreen()
        fileName = 'save/temp/' + str(self.page) + '.jpg'
        pix.save(fileName)
        print('截图并保存成功')

    def paintEvent(self, event):
        '''绘图事件'''

        # 绘制在屏幕上

        painter_to_window = QPainter(self)
        painter_to_window.setRenderHint(QPainter.Antialiasing, True)  # 反锯齿
        painter_to_window.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter_to_window.drawPixmap(0, 0, self.pix)

    def mousePressEvent(self, event):

        # 鼠标左键按下
        if event.button() == Qt.LeftButton:
            self.isWritten = True  # 当前页有输入或改动
            self.isWritting = True  # 已开始抒写
            self.lastPoint = event.pos()
            self.endPoint = self.lastPoint
            logger.debug('点击左键')

            g_hw_render.insert_first(event.pos().x(), event.pos().y())

    def mouseMoveEvent(self, event):
        '''
            调用update()函数在这里相当于调用paintEvent()函数
        '''

        if event.buttons() and Qt.LeftButton:
            self.endPoint = event.pos()
            # 进行重新绘制
            logger.debug('鼠标移动')
            g_hw_render.insert(event.pos().x(), event.pos().y())
            self.draw()  # 绘制
            self.update()

    def mouseReleaseEvent(self, event):

        # 鼠标左键释放
        if event.button() == Qt.LeftButton:
            self.endPoint = event.pos()
            # 进行重新绘制

            g_hw_render.insert_last(event.pos().x(), event.pos().y())
            self.draw()  # 绘制
            self.update()
            self.isWritting = False  # 已停止抒写
            logger.debug('左键释放')

    def draw(self):
        logger.debug('draw')

        painter = QPainter(self.pix)
        # pen = QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.setPen(self.pen)
        painter.begin(self.pix)
        self.drawPath(painter)
        painter.end()

        self.update()

    def drawPath(self, painter):

        m_cur_path = g_hw_render.get_m_cur_path()
        start_index = 0
        if m_cur_path.len > 11:
            start_index = m_cur_path.len - 11
        else:
            start_index = 0
        for p in range(start_index, m_cur_path.len - 1):
            # print(i)
            # print("输出所有点和宽度(%d,%d)_%f" % (m_cur_path._point[p].p.x, m_cur_path._point[p].p.y, m_cur_path._point[p].w))
            point1 = QPoint(m_cur_path._point[p].p.x, m_cur_path._point[p].p.y)
            point2 = QPoint(m_cur_path._point[p + 1].p.x, m_cur_path._point[p + 1].p.y)
            w = m_cur_path._point[p].w
            if self.eraseable == True:
                self.pen.setWidth(100)  # 设置黑板擦宽度
            else:
                # 改变笔的粗细
                self.pen.setWidthF(w * 25)
                pass
            painter.setPen(self.pen)
            painter.drawLine(point1, point2)
        logger.debug('drawPath')

    def keyPressEvent(self, event):
        '''
        键盘事件
        :param event:
        :return:
        '''

        key = event.key()
        # ESC最小化白板
        if key == Qt.Key_Escape:
            self.hide()
        elif key == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.applyForMeetingNum()  # 申请会议号

        elif key == Qt.Key_F5:
            # 开启分享
            global is_share
            if not is_share:
                is_share = True
                self.setWindowTitle("白板 - 分享已开启@" + self.meetingNumber)

            elif is_share and self.shareThread.is_alive():
                is_share = False
                self.setWindowTitle("白板 - 分享已关闭")

    def contextMenuEvent(self, event):
        '''
        白板中的右键菜单
        :param event:
        :return:
        '''

        qmenu = QMenu(self)

        qmenu.addAction('清屏', self.clearScree)

        savePictureAct = qmenu.addAction('保存')
        savePictureAct.triggered.connect(lambda: self.savePicture(False))
        qmenu.addAction('切换', self.switch)

        qmenu.addSeparator()
        qmenu.addAction('上一页', self.previousPage)
        qmenu.addAction('下一页', self.nextPage)
        qmenu.addSeparator()

        self.changeColorBlack = qmenu.addAction('黑笔')
        self.changeColorBlack.triggered.connect(lambda: self.changeColor(0))
        self.changeColorBlue = qmenu.addAction('蓝笔')
        self.changeColorBlue.triggered.connect(lambda: self.changeColor(1))
        self.changeColorRed = qmenu.addAction('红笔')
        self.changeColorRed.triggered.connect(lambda: self.changeColor(2))
        qmenu.addAction('擦除', self.erase)
        qmenu.addSeparator()

        # self.changeThickness = qmenu.addAction('笔的粗细', self.changeThickness())
        # qmenu.addSeparator()

        # qmenu.addAction('功能', self.startSharing)
        # qmenu.addAction('恢复', self.restorePicture)
        # qmenu.addAction('加载', self.loadPicture)

        self.action = qmenu.exec_(self.mapToGlobal(event.pos()))

    def loadPicture(self):
        # 加载本地图片
        pass

    def restorePicture(self):
        pass

    def startSharing(self):
        pass

    def changeThickness(self):
        pass

    def erase(self):

        if self.eraseable == False:
            self.eraseable = True
            self.pen.setColor(Qt.white)  # 设置黑板擦的颜色为白色，与画板颜色一致
            self.pen.setWidth(100)  # 设置黑板擦宽度
            # self.paint_to_pix.setPen(self.pen) # 更新paint_to_pix
            self.penColor = 3
        else:
            self.eraseable = False
            self.changeColor(0)

    def changeColor(self, colorNum):
        '''
        换颜色
        :param colorNum: 颜色号
        :return:
        '''

        # 关闭黑板擦
        self.eraseable = False

        # 笔的颜色
        colorDic = {0: Qt.black, 1: Qt.blue, 2: Qt.red}

        self.pen.setColor(colorDic[colorNum])
        self.penColor = colorNum
        # self.pen.setWidth(4)  # 设置固定宽度

    def nextPage(self):
        '''
        切换下一页画布
        :return:
        '''
        print('下一页1')
        if self.isWritten:
            # 当前页有输入或改动则保存当前页
            self.savePicture(True)
            # self.pos_pages[self.page] = self.pos_xyc  # 记录当前页笔画路径
            self.isWritten = False  # 关闭改动标志
            print('下一页2')

        if self.page == self.pages:

            # 开辟新一页，总页数加一
            # self.pos_xyc = []  # 当前页路径清空
            self.pages += 1  # 页总数加一
            self.pix.fill(Qt.white)  # 清空画布

        else:
            # 当前页并非最后一页
            print('下一页3')
            fileName = str(self.page + 1)
            readFileName = os.path.join(self.filePath, 'temp', fileName + '.jpg')
            QPixmapCache.clear()
            self.pix.load(readFileName)

            # self.pos_xyc = self.pos_pages[self.page + 1]
        print('下一页4')

        self.update()  # 更新内容
        print('下一页5')

        self.page = self.page + 1  # 当前页码加一
        print('下一页6')

        # t_changName = threading.Thread(target=self.changeWinName, args=(self.page, self.pages,))
        # t_changName.start()
        # self.setWindowTitle('当前' + str(self.page) + '/' + str(self.pages) + '页')  # 更新标题栏显示的页码
        print('下一页7')

        logger.debug('下翻页第%s页', self.page)

    def changeWinName(self, page, pages):
        self.setWindowTitle('当前' + str(page) + '/' + str(page) + '页')  # 更新标题栏显示的页码

    def previousPage(self):
        '''
        切换到上一页画布
        :return:
        '''

        if self.isWritten or (self.page == self.pages):
            # 当前页有输入或改动则保存当前页
            self.savePicture(True)
            # self.pos_pages[self.page] = self.pos_xyc  # 记录当前页笔画路径
            self.isWritten = False  # 关闭改动标志

        if self.page > 1:
            # 当前页码非第一页
            self.page -= 1  # 当前页码减一
            fileName = str(self.page)
            readFileName = os.path.join(self.filePath, 'temp', fileName + '.jpg')
            QPixmapCache.clear()  # 清空画布
            self.pix.load(readFileName)

            # self.pos_xyc = self.pos_pages[self.page]

        else:
            # 当前页码为第一页
            pass

        self.update()  # 更新内容
        print('下一页6')

        # self.setWindowTitle('当前' + str(self.page) + '/' + str(self.pages) + '页')  # 更新标题栏显示的页码
        # t_changName = threading.Thread(target=self.changeWinName, args=(self.page, self.pages,))
        # t_changName.start()
        logger.debug('上翻页第%s页', self.page)

    def switch(self):
        '''切换'''

        self.showMinimized()

    def savePicture(self, flag=True, meetingID='201711'):
        '''
            将当前白板上的内容保存成图片
            flag = True,为自动保存
            flag = False为用户保存
        '''
        # 保存目录 './save/日期+会议号/'
        time = QDateTime.currentDateTime().toString("yyyy-MM-dd_")
        self.meetingID = meetingID
        self.filePath = os.path.join(os.getcwd(), 'save', time + self.meetingID)
        # 创建目录
        if not os.path.exists(self.filePath):
            os.makedirs(self.filePath)
            os.makedirs(os.path.join(self.filePath, 'temp'))

        if flag:

            # 自动保存分为两部分：1.保存图片到本地 2.保存保存路径json文件到本地
            # 1.保存图片到本地
            # fileName = QDateTime.currentDateTime().toString('yyMMddhhmmss')
            fileName = str(self.page)  # 以页码为图片名
            logger.debug('filePath %s', os.path.join(self.filePath, 'temp', fileName + '.jpg'))
            self.pix.save(os.path.join(self.filePath, 'temp', fileName + '.jpg'))
            logger.debug('保存图片')

            # 2.保存保存路径json文件到本地
            import json
            dict = {'pox_xyc': self.pos_xyc,
                    'page': self.page,
                    'meetingID': self.meetingID
                    }
            # logger.debug('dict: %s', dict)

            with open(os.path.join(self.filePath, 'temp', fileName + '.json'), 'w') as f:
                json.dump(dict, f)
            logger.debug('保存json文件')

        else:

            # 用户手动保存
            fileName = QFileDialog.getSaveFileName(self, '保存图片', self.filePath, ".png;;.jpg")
            self.pix.save(fileName[0] + fileName[1])

    def clearScree(self):
        '''清屏'''

        # self.pos_xyc.clear()
        self.update()
        self.pix.fill(Qt.white)

    def closeEvent(self, QCloseEvent):
        '''
        关闭白板时保存当前画板内容
        :return:
        '''
        print('关闭白板')
        qApp.quit()  # 强制关闭


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dbb = DrawingBoardUIBusi()
    dbb.show()
    sys.exit(app.exec_())
