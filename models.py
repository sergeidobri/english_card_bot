"""
Данный модуль является дополнением к телеграмм-боту. 
Здесь происходит определение моделей (таблиц) в базе
данных. Также здесь представлены некоторые функции по
работе с ней.
"""

import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import or_

Base = declarative_base()

class Words(Base):
    """
    Определяет модель для хранения слов в базе данных.

    Атрибуты:
        id (int): Уникальный идентификатор записи.
        target (str): Слово на иностранном (английском) языке.
        translation (str): Перевод целевого слова на русский язык.

    Связи:
        vocabulary: Связь с моделью Vocabulary.

    """
    __tablename__ = "words"

    id = sq.Column(sq.Integer, primary_key=True)
    target = sq.Column(sq.String(length=120), nullable=False)
    translation = sq.Column(sq.String(length=120), nullable=False)

    vocabulary = relationship("Vocabulary", back_populates="word")

    def __str__(self):
        return f"Words pair {self.id}: {self.target} - {self.translation}"


class Users(Base):
    """
    Определяет модель для хранения пользователей в базе данных.

    Атрибуты:
        id (int): Уникальный идентификатор пользователя.
        tg_id (int): Уникальный идентификатор пользователя в Telegram.
        name (str): Имя пользователя.

    Связи:
        vocabulary: Связь с моделью Vocabulary.

    """
    __tablename__ = "users"

    id = sq.Column(sq.Integer, primary_key=True)
    tg_id = sq.Column(sq.BigInteger, unique=True, nullable=False)
    name = sq.Column(sq.String(length=75), nullable=True)

    vocabulary = relationship("Vocabulary", back_populates="user")

    def __str__(self):
        return f"User {self.id}: {self.name}. tg_id {self.tg_id}"

class Vocabulary(Base):
    """
    Определяет модель для хранения словарных записей, связывая 
    пользователей и пары слов (англ - рус).

    Атрибуты:
        id (int): Уникальный идентификатор записи.
        user_id (int): Идентификатор пользователя из таблицы users.
        word_id (int): Идентификатор пары слов из таблицы words.

    Связи:
        word: Связь с моделью Words.
        user: Связь с моделью Users.

    """
    __tablename__ = "vocabulary"

    id = sq.Column(sq.Integer, primary_key=True)
    user_id = sq.Column(sq.Integer, sq.ForeignKey("users.id"), nullable=False)
    word_id = sq.Column(sq.Integer, sq.ForeignKey("words.id"), nullable=False)

    word = relationship("Words", back_populates="vocabulary")
    user = relationship("Users", back_populates="vocabulary")


def create_tables(engine):
    """
    Создает таблицы в базе данных, если они не существуют.

    Параметры:
        engine: SQLAlchemy engine, который используется для подключения
                к базе данных.

    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def fill_db_with_default_data(session):
    """
    Заполняет базу данных начальными данными.

    Параметры:
        session: SQLAlchemy session для выполнения операций с базой данных.

    """
    if len(list(session.query(Users).filter(Users.tg_id==0).all())) == 0:
        everybody = Users(tg_id=0, name="everybody")
        session.add(everybody)
        session.commit()
        words = [
            ("vitamin", "витамин"),
            ("oven", "духовка"),
            ("silk", "шелк"),
            ("jacket", "куртка"),
            ("soda", "газировка"),
            ("shower", "душ"),
            ("sword", "меч"),
            ("vampire", "вампир"),
            ("widow", "вдова"),
            ("stick", "палка"),
        ]
        for target, translate in words:
            word = Words(target=target, translation=translate)
            vocabulary = Vocabulary(word=word, user=everybody)
            session.add_all([word, vocabulary])
        session.commit()

def get_words_list(session, user_id):
    """
    Возвращает список слов и их переводов для указанного пользователя.

    Параметры:
        session: SQLAlchemy session для выполнения операций с базой данных.
        user_id (int): Идентификатор пользователя для поиска слов.

    Возвращает:
        list: Список кортежей, содержащих целевые слова и их переводы.

    """
    return list(session.query(Words.target, Words.translation).\
                    select_from(Words).\
                        join(Vocabulary, Words.id == Vocabulary.word_id).\
                        join(Users, Vocabulary.user_id == Users.id).\
                            filter(or_(Users.tg_id == user_id,
                                       Users.tg_id == 0)))
