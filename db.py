import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()
engine = sq.create_engine('вставьте сюда путь к вашей базе данных')
Session = sessionmaker(bind=engine)
session = Session()


# Таблица "User", где будет храниться вся информация по пользователю
class User(Base):
    __tablename__ = 'user'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    range_age = sq.Column(sq.String)
    city = sq.Column(sq.String)


# Таблица "DatingUser", где будут храниться все найденные пары для пользователя
class DatingUser(Base):
    __tablename__ = 'datinguser'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    id_User = sq.Column(sq.Integer, sq.ForeignKey('user.id'))
    user = relationship(User)


# Создать пустые таблицы в БД если их нет
def create_tables():
    Base.metadata.create_all(engine)


# Добавляем пользователя в БД
def add_user(user):
    session.expire_on_commit = False
    session.add(user)
    session.commit()


# Показать всех понравившихся людей из БД
def view_all(user_id):
    links = []
    id_query = session.query(User.id).order_by(User.id.desc()).filter(User.vk_id == user_id).limit(1)
    id_list = [p.id for p in id_query]
    id_user = id_list[0]
    dating_users_query = session.query(DatingUser.vk_id).filter(DatingUser.id_User == id_user).all()
    dating_users_list = [du.vk_id for du in dating_users_query]
    for link in dating_users_list:
        links.append(link)
    return links


# Удаляем пользователя из БД
def delete_user(dating_user_id):
    session.expire_on_commit = False
    session.query(DatingUser).filter(DatingUser.vk_id == dating_user_id).delete()
    session.commit()
