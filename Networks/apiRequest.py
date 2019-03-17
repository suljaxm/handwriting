#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by GJ on 2018/1/21
import json
import threading
import urllib

import functools
import requests
import logging

from PyQt5.QtCore import QThread, pyqtSignal
from contextlib import contextmanager
from urllib import error

from requests import Response
from requests.cookies import RequestsCookieJar

logger = logging.getLogger(__name__)

baseUrl = 'http://akim.3w.dkys.org'
url_newMettingNum = baseUrl + '/api/connect/newMeeting.html'
url_connect = baseUrl + '/api/connect/delay/'
url_uploadPic = baseUrl + '/api/connect/upload/'
url_savePic = baseUrl + '/api/page/save/'
url_login = baseUrl + '/api/user/login.html'
url_sign = baseUrl + '/api/user/regist.html'
url_signCode = baseUrl + '/api/user/sendSmsCode.html'  # 验证码固定获取网址
url_forgetCode = baseUrl + '/api/user/confirm/phone.html'  # 验证码固定获取网址
url_chgPass = baseUrl + '/api/user/sendSmsCode.html'
url_applytMeetingNum = baseUrl + '/api/connect/newMeeting.html'
url_code = baseUrl + '/api/user/code.html'  # 图形验证码

# TCP重传需要3秒。
default_timeout = 15

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'Accept-Language': 'zh-CN,zh;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36'
}

cookies = {}


@contextmanager
def ignored(*exception):
    """
    使用上下文管理的方式忽略错误。
    with ignored(OSError):
        print(1)
        raise(OSError)

    print(2)

    """
    if exception:
        try:
            yield
        except exception:
            logger.error("error has ignored.", exc_info=True)
    else:
        try:
            yield
        except:
            logger.error("error has ignored.", exc_info=True)


# 异常处理的装饰器
def requestsExceptionFilter(func):
    """
    若某一函数出错(一般是网络请求), 会再次进行2次重新请求，否则会传回False
    @requestsExceptionFilter
    def test():
        requests.get('http://www.thereAreNothing.com')

    test()
    ---
    False
    """

    def _filter(*args, **kwargs):
        for i in range(3):
            try:
                return func(*args, **kwargs)
            except:
                logger.error("retry function {0} args {1}, kwargs {2} times:{3}".format(func, args, kwargs, i))
                continue
        else:
            logger.error("function {0} is wrong. args {1}, kwargs {2}".format(func, args, kwargs))
            return False

    return _filter


class HttpRequest(object):
    _instance = None

    def __init__(self):
        self.headers = headers.copy()
        self.sessions = requests.session()  # 保持会话状态，复用TCP链接

    def __new__(cls, *args, **kwargs):
        '单例模式'
        if cls._instance == None:
            cls._instance = object.__new__(cls, *args, **kwargs)
            cls._instance.cookies = None
            # print("new instance")
        return cls._instance

    @requestsExceptionFilter
    def get(self, url, **kwargs):
        if not kwargs.get('headers'):
            kwargs['headers'] = self.headers
        return requests.get(url, **kwargs)

    @requestsExceptionFilter
    def post(self, url, **kwargs):
        if not kwargs.get('headers'):
            kwargs['headers'] = self.headers

        return requests.post(url, **kwargs)

    @requestsExceptionFilter
    def httpRequest(self, action, method="GET", add=None, files=None, headers=None, cookie="", \
                    timeout=default_timeout, urlencode='utf-8', is_json=True):
        """
            默认以get方式请求，
            GET方式附加内容用add参数，POST方式提交内容用data参数。
            编码用urlencode参数，默认utf-8。
            默认cookies为空。
        """
        # for o in self.cookies:
        #     print(o)
        # print("=======")
        if self.cookies:
            cookie = self.cookies
        if not headers:
            headers = self.headers

        if method.upper() == 'GET':
            if add:
                html = self.sessions.get(action, params=add, headers=headers, cookies=cookie, timeout=timeout)
            else:
                html = self.sessions.get(action, headers=headers, cookies=cookie, timeout=timeout)
            html.encoding = urlencode

        elif method.upper() == 'POST':
            if files:
                html = self.sessions.post(action, files=files, headers=headers, cookies=cookie, timeout=timeout)
            else:
                html = self.sessions.post(action, params=add, headers=headers, cookies=cookie, timeout=timeout)
            html.encoding = urlencode
        self.cookies = html.cookies.copy()
        return html

    def __del__(self):
        # 关闭请求。
        with ignored():
            self.sessions.close()

    def loginRequest(self, data, func):
        # 登录请求'
        # 创建线程
        print('++++登录请求++')

        self.thread = MyThread(url_login, data, method='POST')
        # 注册信号处理函数
        self.thread._signal.connect(func)
        # 启动线程
        self.thread.start()

    def codeRequest(self, data, func):
        # 获取图形验证码'
        self.thread = MyThread(url_code, data, method='GET', isJson=False)
        print('++++获取图形验证码++')
        self.thread._signal.connect(func)
        self.thread.start()

    def signCodeRequest(self, data, func):
        # 获取注册验证码
        print('++++获取注册验证码++')
        self.thread = MyThread(url_signCode, data)
        self.thread._signal.connect(func)
        self.thread.start()

    def signInRequest(self, data, func):
        # 注册请求
        print('++++注册请求++')
        self.thread = MyThread(url_sign, data, "POST")
        self.thread._signal.connect(func)
        self.thread.start()

    def forgetCodeRequest(self, data, func):
        # 获取忘记密码验证码
        print('++++获取忘记密码验证码++')
        self.thread = MyThread(url_forgetCode, data, method='POST')
        self.thread._signal.connect(func)
        self.thread.start()

    def changePasswdRequest(self, data, func):
        # 修改密码请求
        print('+++修改密码请求+++')
        self.thread = MyThread(url_sign, data)
        self.thread._signal.connect(func)
        self.thread.start()

    def applyMeetingNum(self, data, func):
        # 点击登录后获取会议编号,先得到服务器返回的Data数据，从Data中得到用户ID'
        print('+++点击登录后获取会议编号+++')
        self.thread = MyThread(url_applytMeetingNum, data, method='GET')
        self.thread._signal.connect(func)
        self.thread.start()

    def applyUrlPic(self, ticket, func):
        print('+++获取二维码+++')
        pic_url = 'https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=' + ticket
        self.thread = MyThread(pic_url, data=None, method='GET', isJson=False)
        self.thread._signal.connect(func)
        self.thread.start()

    def applyForMeetingNum(self):

        return self.httpRequest(action=url_newMettingNum, method='GET')

    def meetingConnection(self, meetingId):
        print('+++会议连接+++')
        url = url_connect + meetingId + '.html'
        response = None
        try:
            response = self.httpRequest(action=url, method='GET', timeout=120)
        except:
            response = None

        return response

    def uploadPic(self, files, meetingId='10001', pageNum='1'):
        print('+++上传图片+++')
        url = url_uploadPic + meetingId + '/' + str(pageNum) + '.html'
        return self.httpRequest(action=url, files=files, method='POST')


class MyThread(QThread):
    # 定义信号,定义参数为str类型
    _signal = pyqtSignal(object)

    def __init__(self, url, data, method="GET", isJson=True):
        super(MyThread, self).__init__()
        self.url = url
        self.data = data
        self.method = method
        self.isJson = isJson

    def run(self):
        try:
            resp = HttpRequest().httpRequest(action=self.url, add=self.data, method=self.method)
        except:
            resp = None
        finally:
            print('+++++2222222')
            if resp:
                if self.isJson:
                    self._signal.emit(resp.json())
                else:
                    self._signal.emit(resp)
                    print('++++111111111')
            else:
                if self.isJson:
                    json = {"status": "noNet"}  # 无网络连接下返回
                    self._signal.emit(json)
                else:
                    self._signal.emit(None)


if __name__ == '__main__':
    a = requests.session()
    help(ignored)
    print('\n')
    help(requestsExceptionFilter)
    print('\n')
    help(HttpRequest)
