from flask import current_app
from flask import g
from flask import request
from flask import session,jsonify

from info import constants
from info import db
from info.models import User, News, Category
from info.utils.response_code import RET
from . import admin_blue
from flask import render_template,redirect,url_for
from info.utils.common import user_login_data
import time
from datetime import datetime,timedelta
from info.utils.image_storage import storage

@admin_blue.route('/add_category', methods=["POST"])
def add_category():
    """修改或者添加分类"""
    category_id = request.json.get("id")
    category_name = request.json.get("name")


    if category_id:
        # 如果有分类id说明是需要进行修改
        category = Category.query.get(category_id)
        category.name = category_name
    else:
        category =  Category()
        category.name = category_name

        db.session.add(category)

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "增加分类成功")


"""
新闻分类
"""
@admin_blue.route("/news_type")
def news_type():
    category_list = Category.query.all()
    categories = []
    for category in category_list:
        categories.append(category.to_dict())
    categories.pop(0)
    data = {
        "categories":categories
    }
    return render_template("admin/news_type.html",data = data)







"""
编辑详情

"""
@admin_blue.route("/news_edit_detail",methods = ["GET","POST"])
def news_edit_detail():

    if request.method == "GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)
        category_list = Category.query.all()
        categories = []
        for category in category_list:
            categories.append(category.to_dict())
        categories.pop(0)
        data = {
            "news":news.to_dict(),
            "categories":categories
        }
        return render_template("admin/news_edit_detail.html",data = data)

    news_id = request.form.get("news_id")
    title = request.form.get("title")
    digest = request.form.get("digest")
    content = request.form.get("content")
    index_image = request.files.get("index_image")
    category_id = request.form.get("category_id")
    # 1.1 判断数据是否有值
    if not all([title, digest, content,index_image, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

    index_image = index_image.read()
    key = storage(index_image)

    news = News.query.get(news_id)

    news.index_image_url = constants.QINIU_DOMIN_PREFIX + key

    news.title = title
    news.digest = digest
    news.content = content
    news.category_id = category_id

    # 4. 保存到数据库

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "修改成功")




"""
新闻编辑
"""
@admin_blue.route("/news_edit")
def news_edit():
    page = request.args.get("p", 1)
    keywords = request.args.get("keywords")
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1
    filters = []
    if keywords:
        filters.append(News.title.contains(keywords))
    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, 10, False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    news_list = []
    for user in items:
        news_list.append(user.to_review_dict())
    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }
    return render_template("admin/news_edit.html",data = data)



"""
新闻审核详情
"""
@admin_blue.route("/news_review_detail",methods = ["GET","POST"])
def news_review_detail():
    if request.method == "GET":
        news_id = request.args.get("news_id")
        news = News.query.get(news_id)

        data = {
            "news":news.to_dict()
        }
        return render_template("admin/news_review_detail.html",data = data)
    # 新闻通过审核,新闻没有通过审核
    action = request.json.get("action")
    news_id = request.json.get("news_id")
    news = News.query.get(news_id)
    # 如果当前新闻等于accept表示新闻审核通过
    if action == "accept":
        news.status = 0
    else:
        # 获取到拒绝通过的理由
        reason = request.json.get("reason")
        # 如果拒绝,那么必须给我拒绝的理由
        if not reason:
            return jsonify(errno = RET.PARAMERR,errmsg = "请输入拒绝的理由")
        # 设置拒绝的理由并且把状态设置为-1表示没有通过
        news.status = -1
        news.reason = reason

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "OK")




"""
新闻审核没有通过的新闻或者审核中的新闻
"""
@admin_blue.route("/news_review")
def news_review():
    page = request.args.get("p",1)
    keywords = request.args.get("keywords")
    try:
        page = int(page)
    except Exception as e:  
        current_app.logger.error(e)
        page = 1
    filters = [News.status != 0]
    # 判断用户是否有搜索的关键字
    if keywords:
        filters.append(News.title.contains(keywords))
    # 如果当前的新闻状态等于0 说明已经审核通过
    paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,10,False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    news_list = []
    for user in items:
        news_list.append(user.to_review_dict())

    data = {
        "news_list": news_list,
        "current_page": current_page,
        "total_page": total_page
    }

    return render_template("admin/news_review.html",data = data)









# 获取用户列表
@admin_blue.route("/user_list")
def user_list():
    page = request.args.get("p",1)
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    paginate = User.query.filter(User.is_admin == False).order_by(User.last_login.desc()).paginate(page,10,False)
    items = paginate.items
    current_page = paginate.page
    total_page = paginate.pages
    users = []
    for user in  items:
        users.append(user.to_admin_dict())

    data  = {
        "users":users,
        "current_page":current_page,
        "total_page":total_page
    }

    return render_template("admin/user_list.html",data = data)














@admin_blue.route("/user_count")
def user_count():
    total_count = 0
    mon_count = 0
    day_count = 0
    #　只查询普通用户，因为admin是我们手动添加的，不算潜在的用户
    total_count = User.query.filter(User.is_admin == False).count()
    # 获取到当前时间
    t = time.localtime()
     # 获取到本月的时间
    # 获取到６月１号
    mon_begin = "%d-%02d-01"%(t.tm_year,t.tm_mon)
    # 第一个参数传输时间
    # 第二个参数表示你需要得到的格式化时间
    # 获取到６月１号0分0秒
    mon_begin_date = datetime.strptime(mon_begin,"%Y-%m-%d")

    mon_count = total_count = User.query.filter(User.is_admin == False,User.create_time > mon_begin_date).count()

    # 获取到今天的时间
    day_begin = "%d-%02d-%02d" % (t.tm_year, t.tm_mon,t.tm_mday)
    # 第一个参数传输时间
    # 第二个参数表示你需要得到的格式化时间
    day_begin_date = datetime.strptime(day_begin, "%Y-%m-%d")

    day_count  = User.query.filter(User.is_admin == False, User.create_time > day_begin_date).count()

    # 统计一个月每天用户的增加数量(活跃用户)
    # 往前面倒腾一个月
    # for i range(0,31):
    #     查询一天:User.create_time >= 今日的0点0分0秒  and User.create_time < 今日的23点59分59秒(明天0点0分0秒)
    # # day_count  = User.query.filter(User.is_admin == False,
    # #                                User.create_time >= 今日的0点0分0秒 and User.create_time < 今日的23点59分59秒(明天0点0分0秒)).count()


    # 获取到今天的时间
    # 2018-06-21
    today_begin = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    # 第一个参数传输时间
    # 第二个参数表示你需要得到的格式化时间
    # 2018-06-21- 00:00:00
    today_begin_date = datetime.strptime(today_begin, "%Y-%m-%d")
    active_count = []
    active_time = []
    for i in  range(0,31):
        # 今天的开始时间 2018-06-21- 00:00:00
        begin_date = today_begin_date - timedelta(days = i)
        # 明天的开始时间 2018-06-22- 00:00:00(今天的结束时间 2018-06-21- 23:59:59)
        end_date = today_begin_date - timedelta(days = (i - 1))

        count = User.query.filter(User.is_admin == False,
                User.create_time >= begin_date ,
                                      User.create_time < end_date).count()
        active_count.append(count)
        active_time.append(begin_date.strftime("%Y-%m-%d"))

    active_count.reverse()
    active_time.reverse()
    data = {
        "total_count":total_count,
        "mon_count":mon_count,
        "day_count":day_count,
        "active_count":active_count,
        "active_time":active_time
    }
    return render_template("admin/user_count.html",data = data)




@admin_blue.route("/index")
@user_login_data
def admin_index():
    user = g.user
    return render_template("admin/index.html",user = user.to_dict())



@admin_blue.route("/login",methods = ["GET","POST"])
@user_login_data
def admin_login():
    if request.method == "GET":
       user_id = session.get("user_id",None)
       is_admin = session.get("is_admin",False)
       if user_id  and is_admin:
           return redirect(url_for("admin.admin_index"))
       return render_template("admin/login.html")
    username = request.form.get("username")
    password = request.form.get("password")

    user =  User.query.filter(User.mobile == username,User.is_admin == True).first()
    if not user:
        return render_template("admin/login.html",errmsg = "not user")

    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="not password")

    session["user_id"] = user.id
    session["mobile"] = user.mobile
    session["is_admin"] = True
    session["nick_name"] = user.nick_name
    return redirect(url_for("admin.admin_index"))