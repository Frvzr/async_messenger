from sqlalchemy import create_engine, Table, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import registry, sessionmaker
import datetime
import os
import sys
sys.path.append('../')


class ClientDatabase:
    '''
    Класс - оболочка для работы с базой данных клиента.
    Использует SQLite базу данных, реализован с помощью
    SQLAlchemy ORM и используется классический подход.
    '''
    class KnownUsers:
        '''
        Класс - отображение для таблицы всех пользователей.
        '''
        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        '''
        Класс - отображение для таблицы статистики переданных сообщений.
        '''
        def __init__(self, contact, direction, message):
            self.id = None
            self.contact = contact
            self.direction = direction
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        '''
        Класс - отображение для таблицы контактов.
        '''
        def __init__(self, contact):
            self.id = None
            self.name = contact

    # Конструктор класса:
    def __init__(self, name):
        # Создаём движок базы данных, поскольку разрешено несколько
        # клиентов одновременно, каждый должен иметь свою БД
        # Поскольку клиент мультипоточный необходимо отключить
        # проверки на подключения с разных потоков,
        # иначе sqlite3.ProgrammingError
        path = os.path.dirname(os.path.realpath(__file__))
        db_name = f'client_{name}.db3'
        self.database_engine = create_engine(
            f'sqlite:///{os.path.join(path, db_name)}', echo=False,
            pool_recycle=7200, connect_args={'check_same_thread': False})
        self.mapper_registry = registry()

        # Создаём таблицу известных пользователей
        users = Table('known_users', self.mapper_registry.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )
        # Создаём таблицу истории сообщений
        history = Table('message_history', self.mapper_registry.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('contact', String),
                        Column('direction', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )
                
        # Создаём таблицу контактов
        contacts = Table('contacts', self.mapper_registry.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        # Создаём таблицы
        self.mapper_registry.metadata.create_all(self.database_engine)

        # Создаём отображения
        self.mapper_registry.map_imperatively(self.KnownUsers, users)
        self.mapper_registry.map_imperatively(self.MessageHistory, history)
        self.mapper_registry.map_imperatively(self.Contacts, contacts)

        # Создаём сессию
        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Необходимо очистить таблицу контактов, т.к. при запуске они
        # подгружаются с сервера.
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def contacts_clear(self):
        '''Метод очищающий таблицу со списком контактов.'''
        self.session.query(self.Contacts).delete()

    def add_contact(self, contact):
        '''Метод добавляющий контакт в базу данных.'''
        if not self.session.query(self.Contacts) \
        .filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        '''Метод удаляющий определённый контакт.'''
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def add_users(self, users_list):
        '''Метод заполняющий таблицу известных пользователей.'''
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, contact, direction, message):
        '''Метод сохраняющий сообщение в базе данных.'''
        message_row = self.MessageHistory(contact, direction, message)
        self.session.add(message_row)
        self.session.commit()

    def get_contacts(self):
        '''Метод возвращающий список всех контактов.'''
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        '''Метод возвращающий список всех известных пользователей.'''
        return [user[0] for user in self.session \
            .query(self.KnownUsers.username).all()]

    def check_user(self, user):
        '''Метод проверяющий существует ли пользователь.'''
        if self.session.query(self.KnownUsers) \
            .filter_by(username=user).count():
            return True
        else:
            return False

    def check_contact(self, contact):
        '''Метод проверяющий существует ли контакт.'''
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, contact):
        '''Метод возвращающий историю сообщений с определённым пользователем.'''
        query = self.session.query(self.MessageHistory) \
                .filter_by(contact=contact)
        return [(history_row.contact, history_row.direction,
                 history_row.message, history_row.date)
                for history_row in query.all()]


# отладка
if __name__ == '__main__':
    test_db = ClientDatabase('test1')
