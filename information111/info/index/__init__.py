from flask import Blueprint
"""
index.__init__:只放置首页的蓝图
"""
index_blue = Blueprint("index",__name__)

from . import views