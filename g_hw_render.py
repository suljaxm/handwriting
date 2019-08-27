'''
@author:Created by YJX on 2018/8/6
@file:g_hw_render.py
@desc:
'''
import z_math
import time

min_pen_width = 1.0
max_pen_width = 5.0
m_tmp_path = None  #临时笔迹
m_cur_path = None  #最终笔迹
m_w_max = min_pen_width
m_w_min = max_pen_width
m_arr_listm = None


# 第一次点击获取的坐标点
def insert_first(x, y):
    global m_tmp_path

    point = z_math.z_point_s(x, y)
    if m_tmp_path is not None:
        m_tmp_path = None
        m_tmp_path = z_math.z_new_fpoint_array(24, m_w_max, m_w_min)

    z_math.z_insert_point(m_tmp_path, point)    #将点point加入笔迹m_cur_path中

# 中间获取的坐标点
def insert(x, y):
    global m_tmp_path, m_cur_path

    point = z_math.z_point_s(x, y) #中间点
    if m_tmp_path is None:
        print("m_cur_path为空")
        m_tmp_path = z_math.z_new_fpoint_array(24, m_w_max, m_w_min)

    z_math.z_insert_point(m_tmp_path, point) #将中间点插入笔迹m_cur_path中
    m_cur_path = m_tmp_path

# 最后获得的点
def insert_last(x, y):
    global m_tmp_path, m_cur_path
    if m_tmp_path is None: return

    point = z_math.z_point_s(x, y)
    z_math.z_insert_last_point(m_tmp_path, point) #将点point插入笔迹m_cur_path，进行收尾
    m_cur_path = m_tmp_path

def get_m_cur_path():
    global m_cur_path
    return m_cur_path


