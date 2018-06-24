from flask import Blueprint
"""
user.__init__:只放置个人中心的蓝图
"""
profile_blue = Blueprint("profile",__name__,url_prefix="/user")

from . import views