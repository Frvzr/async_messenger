import sys
try:
    import sqlalchemy
    print(sqlalchemy.__version__)
except ImportError:
    print('Библиотека SQLAlchemy не найдена')
    sys.exit(13)

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import registry
from datetime import datetime


class Database:
    class User:
        def __init__(self, login):
            self.id = None
            self.login = login
            self.info = None
            
        def __repr__(self):
            return "<Client('%s', '%s')>" %(self.login, self.info)

    class UserHistory:
        def __init__(self, user_id, entry_time, ip_address):
            self.id = None
            self.user = user_id
            self.entry_time = entry_time
            self.ip_address = ip_address
            
        def __repr__(self):
            return f'{self.user}: {self.entry_time} - {self.ip_address}'

    class LoginList:
        def __init__(self, user_id, login_id):
            self.id = None
            self.user = user_id
            self.login = login_id
        
    def __init__(self):
        self.engine = create_engine('sqlite:///database.db3', echo=False, pool_recycle=7200)
        self.mapper_registry = registry()
        
        users_table = Table('Users', self.mapper_registry.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('login', String(128), unique=True),
                            Column('info', String(128))
                            )
        
        user_history_table = Table('UserHistory', self.mapper_registry.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id')),
                                   Column('entry_time', DateTime),
                                   Column('ip_address', String(128)))
        
        login_list = Table('LoginList', self.mapper_registry.metadata,
                           Column('id', Integer, primary_key=True),
                           Column('user', ForeignKey('Users.id')),
                           Column('login', ForeignKey('UserHistory.id')))
        
        self.mapper_registry.metadata.create_all(self.engine)
        self.mapper_registry.map_imperatively(self.User, users_table)
        self.mapper_registry.map_imperatively(self.UserHistory, user_history_table)
        self.mapper_registry.map_imperatively(self.LoginList, login_list)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def add_user(self, login, info):
        result = self.session.query(self.User).filter_by(login=login)
        if result.count():
            user = result.first()
        else:
            user = self.User(login, info)
            self.session.add(user)
            self.session.commit()
        print(user)    
    
    def login_user(self, user, ip_address):
        result = self.session.query(self.User).filter_by(login=user)
        
        if result.count():
            user = result.first()
            login_user = self.UserHistory(user.id, datetime.now(), ip_address)
            self.session.add(login_user)
            self.session.commit()
        else:
            user = self.User(user)
            login_user = self.UserHistory(user.id, datetime.now(), ip_address)
            self.session.add(user, login_user)
            self.session.commit()

    def users_list(self):
        query = self.session.query(
            self.User.login,
            self.User.info
        ) 
        return query.all()
    
    def login_list(self, login=None):
        result = self.session.query(self.User.login,
                                    self.UserHistory.entry_time,
                                    self.UserHistory.ip_address,
                                    ).join(self.User)
        if login:
            result = result.filter(self.User.login==login)
        return result.all()
    
if __name__ == '__main__':    
    db = Database()
    db.add_user("Вася", "Василий")
    db.add_user("Admin", "A")
    db.login_user('Вася', '10.0.0.1')
    db.login_user('Alex', '10.0.0.2')
    print(db.login_list())
    print(db.users_list())
    print(db.login_list('Вася'))




