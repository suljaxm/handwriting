'''
@author:Created by YJX on 2018/8/6
@file:z_math.py
@desc:
'''
import math
import time


class z_point_s:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class z_fpoint_s:
    def __init__(self, point=z_point_s(0, 0), w=0):
        self.p = point
        self.w = w


class z_ipoint_s:
    def __init__(self, point=z_point_s(0, 0), t=0):
        self.p = point
        self.t = t


class z_fpoint_array_s:
    def __init__(self, maxwidth=0, minwidth=0, ref=0, len=0, cap=0, last_point=z_point_s(), last_width=0, last_ms=0):
        self._point = list()

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


def z_cubic(f):
    return f * f * f


def z_point_equals(p1, p2):
    if (p1.x == p2.x and p1.y == p2.y):
        return 1
    return 0


def z_keep_fpoint_array(a=z_fpoint_array_s()):
    a.ref = a.ref + 1
    return a


def z_drop_fpoint_array(a):  # 缺少对ref的操作
    a = None


def z_keep_fpoint_arraylist():
    return


def z_drop_fpoint_arraylist():
    return


defualt_max_width = 5.0
default_min_width = 1.0


def z_new_fpoint_array(initsize, maxwidth, minwidth):
    if initsize <= 0: return 0
    a = z_fpoint_array_s()
    for i in range(initsize):
        a._point.append(z_fpoint_s())
    a.ref = 1
    a.len = 0

    if maxwidth < 0 or minwidth < 0 or maxwidth < minwidth:
        maxwidth = defualt_max_width
        minwidth = default_min_width

    a.maxwidth = maxwidth
    a.minwidth = minwidth

    a.cap = initsize
    for i in range(initsize):
        a._point.append(z_fpoint_s())
    return a
    # (maxwidth = 0, minwidth = 0, ref = 0, len = 0, cap = 0, last_width = 0, last_ms = 0):


def z_resize_fpoints_array(a, count):
    if (a is None) or count < 0: return

    for i in range(count):
        a._point.append(z_fpoint_s())
    a.cap = count
    a.len = min(a.cap, a.len)
    return


def z_new_fpoint_arraylist():
    return


def z_fpoint_arraylist_append(l=z_fpoint_arraylist_s(), a=z_fpoint_array_s()):
    node = z_fpoint_arraylist_node_s()
    node._a = z_keep_fpoint_array(a)
    node._n = None

    if (l._first is None):
        l._first = node
    else:
        l._end._n = node
    l._end = node


def z_fpoint_arraylist_append_new(l, max, min):
    a = z_new_fpoint_array(24, max, min)
    return a


def z_fpoint_arraylist_removelast():
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


def z_distance(b, e):
    d = math.sqrt((b.x - e.x) ** 2 + (b.y - e.y) ** 2)
    return d


def z_fpoint_add_xyw(a, x, y, w):
    # if (int(a._point[a.len-1].p.x) == int(x) and int(a._point[a.len-1].p.y) == int(y)):
    # return
    if a.len == a.cap:
        z_auto_increase_fpoints_array(a)

    temp = z_fpoint_s(z_point_s(x, y), w)

    a._point[a.len] = temp
    a.len = a.len + 1


def z_fpoint_add(a, p):
    z_fpoint_add_xyw(a, p.p.x, p.p.y, p.w)


def z_fpoint_differential_add(a, p):
    if a is None:
        print("a is None")
        return

    if a.len == 0:
        z_fpoint_add(a, p)
        return

    max_diff = 0.1
    last = a._point[a.len - 1]
    sp = last.p

    sw = last.w

    n = (int)((math.fabs(p.w - last.w)) / max_diff + 1)

    x_step = (p.p.x - sp.x) / n
    y_step = (p.p.y - sp.y) / n
    w_step = (p.w - sw) / n

    for i in range(0, n - 1):
        sp.x = sp.x + x_step
        sp.y = sp.y + y_step
        sw = sw + w_step
        z_fpoint_add_xyw(a, sp.x, sp.y, sw)

    z_fpoint_add(a, p)


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
        temp = z_point_s(x1, y1)
        pw = z_fpoint_s(temp, w)
        z_fpoint_differential_add(a, pw)
        t = t + f


def z_linewidth(b, e, bwidth, step):
    max_speed = 2.0
    d = z_distance(b.p, e.p)
    s = d / ((e.t - b.t) * 1000)
    if s > max_speed:
        s = max_speed
    w = (max_speed - s) / max_speed
    max_dif = d * step
    if w < 0.05: w = 0.05
    if (math.fabs(w - bwidth) > max_dif):
        if (w > bwidth):
            w = bwidth + max_dif
        else:
            w = bwidth - max_dif
    return w


def z_insert_point(arr, point):
    if arr is None:
        print("arr is None")
        return
    len = arr.len

    zp = point
    if 0 == len:
        p = z_fpoint_s(zp, 0.4)
        z_fpoint_add(arr, p)
        z_fpoint_array_set_last_info(arr, point, p.w)
        return p.w
    # 只有当len大于0的时候才会运行
    cur_ms = time.time()
    last_width = arr.last_width
    last_ms = arr.last_ms
    last_point = arr.last_point
    t_ms = (cur_ms - last_ms) * 1000

    distance = z_distance(point, last_point)

    if t_ms < 60 or distance < 3:
        return

    if arr.len > 4:
        step = 0.05
    else:
        step = 0.2
    bt = z_ipoint_s(last_point, last_ms)
    et = z_ipoint_s(zp, cur_ms)
    w = (z_linewidth(bt, et, last_width, step) + last_width) / 2

    points = z_new_fpoint_array(51, arr.maxwidth, arr.minwidth)

    tmppoint = arr._point[arr.len - 1]
    z_fpoint_add(points, tmppoint)
    if len == 1:
        temp = z_point_s((bt.p.x + et.p.x + 1) / 2, (bt.p.y + et.p.y + 1) / 2)
        p = z_fpoint_s(temp, w)
        z_fpoint_differential_add(points, p)

        w = p.w
    else:
        bw = tmppoint
        c = last_point
        temp = z_point_s((c.x + point.x) / 2, (c.y + point.y) / 2)
        ew = z_fpoint_s(temp, w)
        z_square_bezier(points, bw, c, ew)

    # escape the first point

    for i in range(1, points.len):
        z_fpoint_add(arr, points._point[i])

    points = None

    z_fpoint_array_set_last_info(arr, point, w)
    return w


def z_insert_last_point(arr, e):
    if arr is None:
        print("arr is None")
        return

    len = arr.len
    if len == 0: return
    points = z_new_fpoint_array(51, arr.maxwidth, arr.minwidth)
    last = arr.last_point
    lw = arr.last_width

    z_fpoint_add_xyw(points, last.x, last.y, lw)


    for i in range(0, points.len):
        z_fpoint_add(arr, points._point[i])  # 将points中的点保存在arr中，  arr为 m_cur_path

    points = None


def z_list_new():
    return


def z_list_append_new():
    return


def z_list_remove_last():
    return


def z_list_clear():
    return


def z_list_free():
    return


def z_malloc_array():
    return


def z_resize_array():
    return


def z_fpoint_array_set_last_info(arr=None, last_point=z_point_s(), last_width=0):  # 导入list，出现的问题
    if arr is None: return
    arr.last_point = last_point
    arr.last_ms = time.time()
    arr.last_width = last_width
