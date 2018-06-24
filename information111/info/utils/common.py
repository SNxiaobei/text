from flask import g
from flask import session

from info.models import User
import functools

def index_class(index):
    if index == 0:
        return "first"
    elif index == 1:
        return "second"
    elif index == 2:
        return "third"
    else:
        return ""

def user_login_data(f):
    @functools.wraps(f)
    def wrapper(*args,**kwargs):
        user_id = session.get("user_id")
        # 默认值
        user = None
        if user_id:
            # 根据id查询当前用户
            user = User.query.get(user_id)
        g.user = user
        return f(*args,**kwargs)
    return wrapper



# def user_login_data():
#     """
#         右上角的用户判断是否登陆
#         :param news_id:
#         :return:
#         """
#     # 获取到用户id
#     user_id = session.get("user_id")
#     # 默认值
#     user = None
#     if user_id:
#         # 根据id查询当前用户
#         user = User.query.get(user_id)
#     return user