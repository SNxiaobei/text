
from flask import current_app
from flask import g
from flask import session

from info import db
from info.models import User, News, Comment, CommentLike
from info.utils.common import user_login_data
from info.utils.response_code import RET
from . import news_blue
from flask import render_template,request,jsonify





"""关注与取消关注"""
@news_blue.route("/followed_user", methods=["POST"])
@user_login_data
def followed_user():
    user = g.user
    # 判断用户是否登陆
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登陆")
    user_id = request.json.get("user_id")
    action = request.json.get("action")
    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg="缺少参数")
    if action not in ("follow", "unfollow"):
        return jsonify(errno=RET.PARAMERR, reemsg="参数错误")
    # 查询关注的用户信息
    try:
        target_user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")
    if not target_user:
        return jsonify(errno=RET.NODATA, errmsg="未查询到用户数据")
    # 根据不同操作做不同逻辑
    if action == "follow":
        if target_user.followers.filter(User.id == user.id).count() > 0:
            return jsonify(errno=RET.DATAEXIST, errmsg="当前已关注")
        target_user.followers.append(user)
    else:
        if target_user.followers.filter(User.id == user.id).count() > 0:
            target_user.followers.remove(user)

    db.session.commit()
    return jsonify(errno=RET.OK, errmsg="操作成功")



@news_blue.route("/comment_like",methods = ["POST"])
@user_login_data
def comment_like():
    user = g.user
    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = "请登陆才能点赞")

    comment_id = request.json.get("comment_id")
    news_id = request.json.get("news_id")
    # 用户点赞的动作,add表示点赞,remove表示取消点赞
    action = request.json.get("action")

    """
      需求:评论点赞:
          1 首先得知道是谁点赞,user.id
          2 需要知道当前点的是哪条评论 comment_id
    """
    comment = Comment.query.get(comment_id)

    if action == "add":
        # 点赞
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,CommentLike.user_id == user.id).first()
        if not comment_like:
            # 如果从数据库里面查询出来的值,没有点赞,才能进行点赞,如果已经点赞了,那么就取消点赞
           comment_like = CommentLike()
           comment_like.comment_id = comment_id
           comment_like.user_id = user.id
           db.session.add(comment_like)
           comment.like_count += 1
    else:
        comment_like = CommentLike.query.filter(CommentLike.comment_id == comment_id,
                                                CommentLike.user_id == user.id).first()
        #  取消点赞
        if comment_like:
           db.session.delete(comment_like)
           comment.like_count -= 1

    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "点赞成功")




@news_blue.route("/news_comment",methods = ["POST"])
@user_login_data
def news_comment():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="请登陆")
    news_id = request.json.get("news_id")
    comment_str = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    # 因为我需要评论,所以至少得知道我评论的是哪条新闻
    news = News.query.get(news_id)
    comment = Comment()
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = comment_str
    # 这个地方判断,是因为不可能所有的评论都有父类,只有搞笑的才有
    if parent_id:
        comment.parent_id = parent_id

    db.session.add(comment)
    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "评论成功",data = comment.to_dict())





@news_blue.route("/news_collect",methods = ["POST"])
@user_login_data
def news_collect():
    # 获取用户是否登陆,因为当前接口注意是针对收藏,如果用户都没有登陆,那么下面的代码就没有任何执行意义
    user = g.user
    if not user:
        return jsonify(errno = RET.SESSIONERR,errmsg = "请登陆")
    # 需要收藏的新闻id
    news_id = request.json.get("news_id")
    # 获取到用户的动作,是否收藏
    action = request.json.get("action")

    news = News.query.get(news_id)

    if action == "collect":
       # 收藏
       user.collection_news.append(news)
    else:
        #取消收藏
       user.collection_news.remove(news)
    db.session.commit()
    return jsonify(errno = RET.OK,errmsg = "收藏成功")



@news_blue.route("/<int:news_id>")
@user_login_data
def news_detail(news_id):
    # g对象可以理解成一个盒子,或者一个容器
    user = g.user


    """

     右边的热门新闻排序

    """
    # 获取到热门新闻,通过点击事件进行倒叙排序,然后获取到前面10新闻
    news_model_list = News.query.order_by(News.clicks.desc()).limit(10)
    # 获取到右边10条热门新闻的列表
    news_dict = []

    for news in news_model_list:
        news_dict.append(news.to_dict())

    """
    展示详情页面
    """

    # 展现详情页面的新闻
    news_model = News.query.get(news_id)
    # 点击完成之后,新闻+1,目的是实现右边的热门新闻
    news_model.clicks += 1

    """关注"""
    # 当前登陆用户是否关注过当前新闻作者
    is_followed = False
    if news_model.user and user:
        if news_model.user in user.followed:
            is_followed = True
    """收藏新闻"""
    # 给收藏新闻添加一个标记,默认情况下,所有的新闻都是没有收藏,所以默认设置为false
    is_collected = False
    if user:
        if news_model in user.collection_news:
            is_collected = True

        # if news_model.user.followers.filter(User.id == user.id).count() > 0:
        #     is_followed = True

    """
    查询当前新闻的所有评论
    """
    comment_list = Comment.query.filter(Comment.news_id == news_id).order_by(Comment.create_time.desc()).all()

    """
    获取到所有评论点赞的数据
    """
    comment_likes = []
    comment_like_ids = []
    if user:
       # 查询用户点赞了哪些评论
       comment_likes = CommentLike.query.filter(CommentLike.user_id == user.id).all()
       # 取出来所有点赞的id
       comment_like_ids = [comment_like.comment_id for comment_like in  comment_likes]

    comment_dict_list = []
    for item in comment_list:
       comment_dict = item.to_dict()
       comment_dict["is_like"] = False
       # 判断用户是否点赞该评论
       if item.id in comment_like_ids:
           comment_dict["is_like"] = True
       comment_dict_list.append(comment_dict)



    data = {
        # 需要在页面展示用户的数据,所有需要把user对象转换成字典
        "user_info": user.to_dict() if user else None,
        "click_news_list": news_dict,
        "is_collected":is_collected,
        "is_followed": is_followed,
        "comments":comment_dict_list,
        "news": news_model.to_dict()
    }
    return render_template("news/detail.html",data = data)
