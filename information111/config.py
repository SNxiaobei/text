import redis
"""
整个项目的配置文件全部放到这个位置

"""
class Config(object):

    SECRET_KEY = "fjladkfjalkfjalfkjl"

    SQLALCHEMY_DATABASE_URI = "mysql://xiaobei:8023949@127.0.0.1:3306/information"
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


class DevelopmentConfig(Config):
    # 调试的时候开启debug模式
    DEBUG = True


class ProductionConfig(Config):
    # 生产模式(上线模式)
    DEBUG = False



# 这个是config的配置文件
config_map ={
    "development":DevelopmentConfig,
    "production":ProductionConfig
}
