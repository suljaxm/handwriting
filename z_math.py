'''
@author:Created by YJX on 2018/8/6
@file:z_math.py
@desc:
'''
import math
import time

#点的坐标
class z_point_s:
    def __init__(self, x=0, y=0, w=0, t=0):
        self.x = x
        self.y = y
        self.w = w

#点的坐标+宽度
class z_fpoint_s:
    def __init__(self, point=z_point_s(0, 0), w=0):
        self.p = point
        self.w = w

#点的坐标+当前时间
class z_ipoint_s:
    def __init__(self, point=z_point_s(0, 0), t=0):
        self.p = point
        self.t = t

#笔迹点
class z_fpoint_array_s:
    def __init__(self, maxwidth=0, minwidth=0, ref=0, len=0, cap=0, last_point=z_point_s(), last_width=0, last_ms=0):
        self._point = list() #_point为z_fpoint_s

        self.maxwidth = maxwidth
        self.minwidth = minwidth
        self.ref = ref
        self.len = len
        self.cap = cap
        self.last_point = last_point
        self.last_width = last_width
        self.last_ms = last_ms


class z_fpoint_arraylist_node_s:
    def __init__(self):
        self._a = z_fpoint_array_s()
        self._n = z_fpoint_arraylist_node_s()


class z_fpoint_arraylist_s:
    def __init__(self, ref=0):
        self.ref = ref
        self._first = None
        self._end = None
        self._cur = None


class z_bezier_factors_s:  # 暂时没有使用
    def __init__(self, bezier_step, max_width_diff, max_move_speed, max_linewith):
        self.bezier_step = bezier_step
        self.max_width_diff = max_width_diff
        self.max_move_speed = max_move_speed
        self.max_linewith = max_linewith

def z_square(f):
    return f * f


defualt_max_width = 5.0
default_min_width = 1.0

def z_new_fpoint_array(initsize, maxwidth, minwidth):
    if initsize <= 0: return 0
    a = z_fpoint_array_s()  #开始创建笔迹
    for i in range(initsize):
        a._point.append(z_fpoint_s()) #添加initsize个数量z_fpoint_s
    a.ref = 1   #当前点所在的编号
    a.len = 0   #当前笔迹的长度

    if maxwidth < 0 or minwidth < 0 or maxwidth < minwidth:  #限定笔迹宽度
        maxwidth = defualt_max_width
        minwidth = default_min_width

    a.maxwidth = maxwidth
    a.minwidth = minwidth

    a.cap = initsize #设定笔迹的点容量为initsize个

    return a

def z_resize_fpoints_array(a, count):
    if (a is None) or count < 0: return

    for i in range(count):
        a._point.append(z_fpoint_s())   #笔迹继续添加count个数量z_fpoint_s
    a.cap = count
    a.len = min(a.cap, a.len)
    return


def z_auto_increase_fpoints_array(a):
    cap = (int)(a.cap + (a.cap + 3) / 4)
    z_resize_fpoints_array(a, cap)
    return


def z_movespeed(s, e):
    d = z_distance(s.p, e.p)
    if d == 0:
        return 0
    return d / (e.t - s.t)

#b和e的欧式距离
def z_distance(b, e):
    d = math.sqrt((b.x - e.x) ** 2 + (b.y - e.y) ** 2)
    return d


def z_fpoint_add_xyw(a, x, y, w):

    if a.len == a.cap:  #如果笔迹的长度到达容量，继续增加笔迹a的容量
        z_auto_increase_fpoints_array(a)

    temp = z_fpoint_s(z_point_s(x, y), w)

    a._point[a.len] = temp  #在笔迹a中添加带有宽度的点temp
    a.len = a.len + 1  #笔迹a的真实长度+1


def z_fpoint_add(a, p):
    z_fpoint_add_xyw(a, p.p.x, p.p.y, p.w)


def z_fpoint_differential_add(a, p):
    if a is None:  #确保a不是null
        print("a is None")
        return

    if a.len == 0:
        z_fpoint_add(a, p)
        return

    max_diff = 0.1
    last = a._point[a.len - 1] #取出笔迹a中的末点
    sp = last.p #取出末点的坐标(x,y)

    sw = last.w #取出末点的宽度

    n = (int)((math.fabs(p.w - last.w)) / max_diff + 1) #根据当前点的宽度和笔迹末点的宽度，获得过渡点的个数n

    x_step = (p.p.x - sp.x) / n
    y_step = (p.p.y - sp.y) / n
    w_step = (p.w - sw) / n

    for i in range(0, n - 1):
        sp.x = sp.x + x_step
        sp.y = sp.y + y_step
        sw = sw + w_step
        z_fpoint_add_xyw(a, sp.x, sp.y, sw) #将一堆过渡点添加进笔迹a中

    z_fpoint_add(a, p) #笔迹中的当前点p加入末尾

# 二次Bezier曲线 P0^2 = ((1-t)^2)*P0+2*(t(1-t))*P1+(t^2)*P2
#起始点 b， 终止点e， 控制点c
def z_square_bezier(a, b, c, e):
    if a is None:
        print("a is None")
        return
    f = 0.1
    t = 0.1
    while t < 1.0:
        x1 = z_square(1 - t) * b.p.x + 2 * t * (1 - t) * c.x + z_square(t) * e.p.x
        y1 = z_square(1 - t) * b.p.y + 2 * t * (1 - t) * c.y + z_square(t) * e.p.y
        w = b.w + (t * (e.w - b.w))
        temp = z_point_s(x1, y1) #过渡点(x1,y1)
        pw = z_fpoint_s(temp, w)
        z_fpoint_differential_add(a, pw) #将过渡点pw当作一个点添加到临时笔迹points中
        t = t + f #迭代


def z_linewidth(b, e, bwidth, step): #bwidth为笔迹末点的宽度
    max_speed = 2.0
    d = z_distance(b.p, e.p)
    s = d / ((e.t - b.t) * 1000)  #s为b和e两点间产生的速度
    if s > max_speed:
        s = max_speed
    w = (max_speed - s) / max_speed #计算出的当前点的宽度
    max_dif = d * step
    if w < 0.05: w = 0.05 #限制最小的线宽
    if (math.fabs(w - bwidth) > max_dif): #当计算出的当前点宽度和笔迹末点不同时
        if (w > bwidth): #判断w和笔迹末点的大小，并人为扩大一个max_dif量级的差距
            w = bwidth + max_dif
        else:
            w = bwidth - max_dif
    return w

def z_insert_point(arr, point):
    if arr is None:
        print("arr is None")
        return
    len = arr.len #此时笔迹arr的长度，初始笔迹的长度为0

    zp = point #插入的点
    if 0 == len:
        p = z_fpoint_s(zp, 0.4) #设置插入点的宽度为0.4
        z_fpoint_add(arr, p)    #将p点插入笔迹arr中
        z_fpoint_array_set_last_info(arr, point, p.w) #在笔迹arr中添加最后一个点的坐标，宽度，时间
        return p.w
    # 只有当len大于0的时候才会运行
    cur_ms = time.time()  #获取当前时间
    last_width = arr.last_width #获取笔迹末点的宽度
    last_ms = arr.last_ms #获取笔迹末点的时间
    last_point = arr.last_point #获取笔迹末点坐标(x,y)
    t_ms = (cur_ms - last_ms) * 1000 #获取末点和当前点的时间差
    distance = z_distance(point, last_point) #获取末点和当前点的距离

    if t_ms < 60 or distance < 3: #当distance或t_ms太短时，则不将当前点加入笔迹arr中
        return
    if arr.len > 4:
        step = 0.05
    else:
        step = 0.2

    bt = z_ipoint_s(last_point, last_ms) #将现有笔迹中最后一点取出充当bt
    et = z_ipoint_s(zp, cur_ms) #当前点
    w = (z_linewidth(bt, et, last_width, step) + last_width) / 2 #计算过度点的宽度
    points = z_new_fpoint_array(24, arr.maxwidth, arr.minwidth) #新建临时笔迹points
    tmppoint = arr._point[arr.len - 1] #笔迹arr中的末点
    z_fpoint_add(points, tmppoint) #将笔迹arr中的末点当作笔迹points的头点

    if len == 1: #笔迹arr的长度为1时，即存在一个头点
        temp = z_point_s((bt.p.x + et.p.x + 1) / 2, (bt.p.y + et.p.y + 1) / 2) #新建一个中间过渡点
        p = z_fpoint_s(temp, w) #添加过度点的宽度
        z_fpoint_differential_add(points, p) #将过渡点p当作一个点添加到临时笔迹points中
        w = p.w
    else: #笔迹arr的长度大于1时
        bw = tmppoint #笔迹arr中的末点（x,y），带有宽度
        c = last_point #获取笔迹末点坐标(x,y)
        temp = z_point_s((c.x + point.x) / 2, (c.y + point.y) / 2) #新建一个中间过渡点
        ew = z_fpoint_s(temp, w)  #添加过度点的宽度
        z_square_bezier(points, bw, c, ew)  #将过渡点ew当作一个点添加到临时笔迹points中

    # escape the first point
    for i in range(1, points.len):
        z_fpoint_add(arr, points._point[i]) #将新建的笔迹points添加到笔迹arr中

    points = None
    z_fpoint_array_set_last_info(arr, point, w) #在笔迹arr中添加最后一个点的坐标，宽度，时间
    return w


def z_insert_last_point(arr, e):
    if arr is None:
        print("arr is None")
        return

    len = arr.len #获得笔迹arr的有效长度
    if len == 0: return

    points = z_new_fpoint_array(24, arr.maxwidth, arr.minwidth)  #新建临时笔迹points
    last = arr.last_point #获得笔迹arr的末点(x,y)
    lw = arr.last_width  #获得笔迹arr的末点宽度
    z_fpoint_add_xyw(points, last.x, last.y, lw) #将末点作为新建笔迹points的头点

    for i in range(0, points.len):
        z_fpoint_add(arr, points._point[i])  # 将points中的点保存在arr中，  arr为 m_cur_path

    points = None

def z_fpoint_array_set_last_info(arr=None, last_point=z_point_s(), last_width=0):  # 导入list，出现的问题
    if arr is None: return
    arr.last_point = last_point
    arr.last_ms = time.time()
    arr.last_width = last_width
