from flask import Blueprint
"""
index.__init__:只放置登陆和注册的蓝图
"""
passport_blue = Blueprint("passport",__name__,url_prefix="/passport")

from . import views