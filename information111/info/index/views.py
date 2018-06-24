import logging
from flask import render_template,current_app
from flask import request,jsonify
from flask import session

from info.models import User, News, Category
from info.utils.response_code import RET
from . import index_blue
"""
index.views:只放置首页的业务逻辑
"""
@index_blue.route("/news_list")
def news_list():
    cid = request.args.get("cid","1")
    # 当前页面的数据
    page = request.args.get("page","1")
    # 每个页面有多少条数据
    per_page = request.args.get("per_page","10")
    # 校验数据
    try:
        cid = int(cid)
        page = int(page)
        per_page = int(per_page)
    except Exception as e:
        current_app.logger.error(e)

        # 3. 查询数据并分页
    filters = [News.status == 0]
    # 如果分类id不为1，那么添加分类id的过滤
    if cid != 1:
        filters.append(News.category_id == cid)
    # 第一个参数表示当前是在哪个页面
    # 第二个参数表示当前页面一共有多少条数据
    # # 第三个参数表示没有错误输出 1,2,3,4,5,6
    if cid == 1:
       paginate = News.query.order_by(News.create_time.desc()).paginate(page,per_page,False)
    else:
       paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,per_page,False)
    # 每个页面上面需要展示的数据
    items = paginate.items
    # 当前页面
    current_page = paginate.page
    # 总页数
    total_page = paginate.pages

    news_list = []
    for news in items:
        news_list.append(news.to_dict())
    data = {
        # 表示当前页面需要展示的数据
        "news_dict_li":news_list,
        # 表示当前页面
        "current_page":current_page,
        # 一共有多少个页面
        "total_page":total_page,
        # 分类id
        "cid":cid
    }
    return jsonify(errno = RET.OK,errmsg = "ok",data = data)




@index_blue.route("/favicon.ico")
def xxxx():
    return current_app.send_static_file('news/favicon.ico')

# self.send_static_file



@index_blue.route("/")
def index():
    # 获取到用户id
    user_id = session.get("user_id")
    # 默认值
    user = None
    if user_id:
       # 根据id查询当前用户
       user =  User.query.get(user_id)

    """

    右边的热门新闻排序

    """
    # 获取到热门新闻,通过点击事件进行倒叙排序,然后获取到前面10新闻
    news_model = News.query.order_by(News.clicks.desc()).limit(10)

    news_dict = []

    for news in news_model:
        news_dict.append(news.to_dict())

    """
    最上面的分类数据
    """
    category_model = Category.query.all()

    category_dict = []

    for category in category_model:
        category_dict.append(category.to_dict())

    data = {
        # 需要在页面展示用户的数据,所有需要把user对象转换成字典
        "user_info":user.to_dict() if user else None,
        "click_news_list":news_dict,
        "categories":category_dict
    }
    return render_template("news/index.html",data = data)