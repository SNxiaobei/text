"""
抽取之前代码

"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
import redis


# 创建flask的应用对象
app = Flask(__name__)


class Config(object):
    SECRET_KEY = "fjladkfjalkfjalfkjl"

    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/information11"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IP地址和端口
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # session类型：redis
    SESSION_TYPE = "redis"
    # session的过期时间
    PERMANENT_SESSION_LIFETIME = 86400 * 2
    # 初始化session-redis
    # 这个redis是用户存储flask_session
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST,port=REDIS_PORT)
    # 开启session签名
    SESSION_USE_SIGNER = True


app.config.from_object(Config)

db = SQLAlchemy(app)


# 创建redis连接对象
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)


Session(app)

# 为flask补充csrf防护
CSRFProtect(app)


@app.route("/index")
def index():
    return "index page"


manager = Manager(app)
Migrate(app,db)
manager.add_command("mysql",MigrateCommand)



if __name__ == '__main__':
    manager.run()
