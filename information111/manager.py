from flask_migrate import Migrate,MigrateCommand
from flask_script import Manager
from info import create_app,db, redis_store
from info import models
from info.models import User

"""
manager的作用只是程序的入口，用来运行程序

"""
# redis_store
app = create_app("development")
manager = Manager(app)
Migrate(app,db)
manager.add_command("mysql",MigrateCommand)
@manager.option("-n", "--name", dest="name")
@manager.option("-p", "--password", dest="password")
def create_super_user(name, password):
    user = User()
    user.nick_name = name
    user.password = password
    user.mobile = name
    user.is_admin = True
    db.session.add(user)
    db.session.commit()





if __name__ == '__main__':
    # print(app.url_map)
    manager.run()