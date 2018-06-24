import random
import re

from flask import current_app
from flask import request,jsonify,make_response
from datetime import datetime

from flask import session

from info import constants, db
from info import redis_store
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_blue
"""
index.views:只放置登陆注册的业务逻辑
"""
'''
退出
'''
@passport_blue.route("/logout")
def logout():
    # 退出,清空session里面的数据
    session.pop("mobile",None)
    session.pop("user_id",None)
    session.pop("nick_name",None)
    session.pop("is_admin", None)
    return jsonify(errno = RET.OK,errmsg = "退出成功")


'''
登陆
'''

@passport_blue.route("/login" ,methods = ["POST"])
def login():
    mobile = request.json.get("mobile")
    # ctrl + d 复制
    password = request.json.get("password")

    user = User.query.filter(User.mobile == mobile).first()

    if not user:
        return jsonify(errno = RET.NODATA,errmsg = "请注册")

    # 检查密码是否正确
    if not user.check_password(password):
        return jsonify(errno = RET.PARAMERR,errmsg = "请输入正确的密码")

    db.session.commit()

    # 把用户注册的数据设置给session

    session["mobile"] = user.mobile
    session["user_id"] = user.id
    session["nick_name"] = user.mobile

    # 最后用户登陆的时间
    user.last_login = datetime.now()



    return jsonify(errno = RET.OK,errmsg = "登陆成功")






@passport_blue.route("/register",methods = ["POST"])
def register():
    mobile = request.json.get("mobile")
    # 用户输入的手机验证码
    smscode = request.json.get("smscode")
    password = request.json.get("password")

    # if not re.match("1[345678]\d{9}",mobile):
    #     return jsonify(errno = RET.PARAMERR,errmsg = "手机号码输入错误")

    # 校验手机验证码
    # 从redis里面获取数据里面缓存的手机验证码
    redis_sms_code = redis_store.get("code_"+mobile)

    if redis_sms_code != smscode:
        return jsonify(errno = RET.PARAMERR,errmsg = "验证码输入错误")

    user = User()
    user.mobile = mobile
    user.nick_name = mobile
    user.password = password
    # datetime.now() 获取到当前的时间,存储到数据库
    user.last_login = datetime.now()
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
    # 把用户注册的数据设置给session
    session["mobile"] = user.mobile
    session["user_id"] = user.id
    session["nick_name"] = user.mobile
    return jsonify(errno = RET.OK,errmsg = "注册成功")



@passport_blue.route("/sms_code" ,methods = ["POST"])
def sms_code():
    print("前端发送过来的地址 = " + request.url)
    # 获取用户在注册页面填写的手机号
    mobile = request.json.get("mobile")
    # 获取用户在注册页面填写的图片验证码
    image_code = request.json.get("image_code")
    # 获取到跟图片验证码一一绑定在一起id
    image_code_id = request.json.get("image_code_id")

    # 从redis服务器获取到uuid
    redis_image_code = redis_store.get("sms_code_" + image_code_id)

    if not redis_image_code:
        return jsonify(errno = RET.NODATA,errmsg = "图片验证码过期")

    # 判断用户输入的验证码是否有问题
    # lower()提高用户体验,把用户输入的值和服务器的值全部小写
    if image_code.lower() != redis_image_code.lower():
        return jsonify(errno = RET.PARAMERR,errmsg = "验证码输入错误")

    # 随机生成验证码
    result = random.randint(0,999999)
    # 保持验证码是6位
    sms_code  = "%06d"%result
    print("短信验证码 = " + sms_code)
    # 存储后端随机生成的短信验证码
    redis_store.set("code_"+mobile,sms_code,300)

    # 发送短信
    # 第一个参数发送给哪个手机号,最多一次只能发送200个手机号,通过,分割
    # 第二个参数是数组形式进行发送[sms_code,100],数组里面的第一个参数表示随机验证码,第二个参数表示多久过期,单位是分钟
    # 第三个参数表示模板id 默认值表示1
    # statusCode = CCP().send_template_sms(mobile,[sms_code, 5],1)
    #
    # if statusCode != 0:
    #     return jsonify(errno = RET.THIRDERR,errmsg = "发送短信失败")

    return jsonify(errno = RET.OK,errmsg = "发送短信成功")





# 双击shift
# 生成图片验证码
@passport_blue.route("/image_code")
def index():
    code_id = request.args.get("code_id")
    if not code_id:
        # 返回值是文档规定必须这样返回
        return jsonify(errno = RET.PARAMERR,errmsg = "参数错误")
    # 获取到图片验证码
    # name:表示图片验证码的名字
    # text:表示图片验证码里面的内容
    # image:这个是验证码的图片
    name, text, image =  captcha.generate_captcha()
    print("图片验证码的内容 = " + text)
    # 获取到验证码之后,存储到redis数据库当中
    # 第一个参数表示name
    # 第二个参数表示验证码里面具体的内容
    # 第三个参数是redis的过期时间,单位是秒
    redis_store.set("sms_code_" + code_id,text,constants.SMS_CODE_REDIS_EXPIRES)
    # 初始化一个响应体
    resp = make_response(image)
    return resp