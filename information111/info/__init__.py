import logging
from logging.handlers import RotatingFileHandler

from flask import g
from flask import render_template

from flask import Flask
from config import Config, DevelopmentConfig,ProductionConfig,config_map
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import generate_csrf
"""

info.__init__:放整个项目模块里面的所有业务逻辑需要用到的一些值

"""


# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG) # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

db = SQLAlchemy()
redis_store = None # type:redis.StrictRedis

# 需求：当init代码完成之后，尽可能不要取动这个里面的代码
# 由于这个地方必须动态传入config的名字，
# 所以必须创建一个函数,但是函数创建之后，
# app对象就被隐藏　
def create_app(config_name):
    app = Flask(__name__)

    class_name = config_map.get(config_name)

    app.config.from_object(class_name)
    db.init_app(app)
    global redis_store
    # 当前这个redis是用来存储对象用的
    redis_store = redis.StrictRedis(host=class_name.REDIS_HOST,port=class_name.REDIS_PORT,decode_responses=True)

    # 设置session
    Session(app)
    # 开启CSRF保护
    CSRFProtect(app)

    # 往浏览器写入csrf_token
    @app.after_request
    def after_request(response):
        # 调用函数生成 csrf_token
        csrf_token = generate_csrf()
        # 通过 cookie 将值传给前端
        response.set_cookie("csrf_token", csrf_token)
        return response

    from info.utils.common import index_class
    app.add_template_filter(index_class, "indexClass")

    # 这个下面会放置所有的蓝图
    from info.index import index_blue
    app.register_blueprint(index_blue)

    # 这个下面会放置所有的蓝图
    from info.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 这个下面会放置所有的蓝图
    from info.news import news_blue
    app.register_blueprint(news_blue)

    # 这个下面会放置所有的蓝图
    from info.user import profile_blue
    app.register_blueprint(profile_blue)

    from info.admin import admin_blue
    app.register_blueprint(admin_blue)

    #  当前的４０４页面表示全局所有的，所以把当前代码写到__init__     
    #  errorhandler：表示捕获http异常
    from info.utils.common import user_login_data

    @app.errorhandler(404)
    @user_login_data
    def not_found(e):
        user = g.user
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("news/404.html", data=data)

    return app

