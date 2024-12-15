"""Основной модуль для работы с тг-ботом"""
import os.path
from random import shuffle
import requests
import telebot
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import or_
from telebot.handler_backends import State, StatesGroup
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
from models import Words, Users, Vocabulary
from models import create_tables, fill_db_with_default_data, get_words_list

### ОПРЕДЕЛЕНИЕ ГЛОБАЛЬНЫХ ПЕРЕМЕННЫХ
PATH = "config.env"

if os.path.exists(PATH):
    load_dotenv(PATH)
else:
    raise FileNotFoundError("Файл не был найден")

TOKEN = os.getenv("TOKEN")
login = os.getenv("LOGIN")
password = os.getenv("PASSWORD")
host = os.getenv("HOST")
db_name = os.getenv("DATABASE_NAME")
port = os.getenv("PORT")
TRANSLATE_TOKEN = os.getenv("TRANSLATE_TOKEN")

bot = telebot.TeleBot(TOKEN)
DSN = f'postgresql://{login}:{password}@{host}:{port}/{db_name}'
engine = sqlalchemy.create_engine(DSN)
Session = sessionmaker(bind=engine)

create_tables(engine)  # создание таблиц бд, учебная вещь

SESSION = Session()
fill_db_with_default_data(SESSION)
SESSION.close()
### ОПРЕДЕЛЕНИЕ ГЛОБАЛЬНЫХ ПЕРЕМЕННЫХ

class Commands:
    """Класс для хранения команд пользователя"""
    REFUSE_NAME_ENTER = "Отказаться вводить имя"
    ADD = "Добавить слово"
    DELETE = "Удалить слово"
    TRAIN = "Тренироваться"
    HELP = "Справкаℹ️"
    MY_DICTIONARY = "Мой словарь"
    YES = "Да✅"
    NO = "Нет❌"
    STOP_TRAINING = "Остановиться"
    LET_TRANSLATE = "Переведи мое слово сам"

class MyStates(StatesGroup):
    """Класс для хранения состояний бота для пользователя"""
    default = State()
    waiting_for_name = State()
    waiting_for_target_word = State()
    waiting_for_translation = State()
    waiting_word_to_del = State()
    training = State()
    training_check = State()

class BotMessages:
    """Класс для хранения сообщений бота"""
    WELCOME = """
👋 Привет! Я ваш помощник в изучении английских слов!

✨ Вот что я умею:

1. Добавлять новые слова для изучения: Скажите мне слово, и я сохраню его для вас, чтобы вы могли учить его позже!
   
2. Удалять слово после его полного изучения: Когда вы почувствуете, что освоили слово, дайте мне знать, и я удалю его из вашего списка.

3. Практиковаться над уже существующими словами: Я помогу вам освежить память и потренироваться с вашими словами, которые вы уже добавили.

Начнем учить новые слова? 💪📚 Перед началом, я бы хотел знать, как вас называть! Пожалуйста, напишите своё имя
"""
    WELCOME_AGAIN = """
👋 Рад снова вас видеть! Я ваш помощник в изучении английских слов!

✨ Вот что я умею:

1. Добавлять новые слова для изучения: Просто отправьте мне слово, и я сохраню его для вас, чтобы вы могли учить его позже!
   
2. Удалять слово после его полного изучения: Когда вы почувствуете, что освоили слово, дайте мне знать, и я удалю его из вашего списка.

3. Практиковаться над уже существующими словами: Я помогу вам освежить память и потренироваться с вашими словами, которые вы уже добавили.

Начнем учить новые слова? 💪📚
"""
    WAITING_NEW_WORD_ENG = """
Пожалуйста, введите новое слово для изучения по-английски🇬🇧​​
"""
    WAITING_NEW_WORD_RUS = """
Пожалуйста, введите перевод этого слова на русский язык🇷🇺​​
"""
    ANSWER_FOR_ANON = """
Понимаю! Важно быть осторожным в сети 🕵️‍♂️. Давай начнём учить новые слова вместе? 📚😊
"""
    ANSWER_FOR_USER = """
Привет! 😊 Я рад с тобой познакомиться, {}! Давай начнем учить слова и весело проведем время! 🎉✨
"""
    INVALID_TARGET_WORD = """
К сожалению, это слово не подходит! 😔

Но не переживайте, попробуйте ввести слово еще раз! 😊 

Обратите, пожалуйста, внимание: слово должно состоять только из латинских букв (а также допустим символ дефиса)
"""
    INVALID_TRASLATION = """
К сожалению, это слово - не перевод на английский! 😔

Но не переживайте, попробуйте ввести слово еще раз! 😊 

Обратите, пожалуйста, внимание: слово должно состоять только из букв кириллицы (а также допустим символ дефиса)
"""
    WORD_SUCCESS_ADDED = """
Отлично!😊 Пара слов {} - {} была успешно добавлена! Выбирайте, что будем делать сейчас?
"""
    WAITING_DEL_WORD_ENG = """
Давайте выберем слово, которое вы хорошо знаете и уже не хотите изучать!
"""
    SUCCESS_DELETE_WORD = """
Слово было успешно удалено. Командуйте, что мы делаем дальше?
"""
    FAILURE_DELETE_WORD = """
Вы такое слово не добавляли!
"""
    TRAINING_MODE = """
Добро пожаловать в режим тренировки! 🎉

Сегодня мы будем учиться новым словам и улучшать ваши навыки перевода. Готовы?
"""
    TRAINING_MODE_ITERATION = """
Ваше слово - {}. Укажите правильный перевод!
"""
    STOP_TRAINING = """
Хорошо! Скажите мне, когда будете готовы потренироваться 💪
"""
    CORRECT_ANSWER = """
Замечательно! Это правильный ответ✅
"""
    INCORRECT_ANSWER = """
К сожалению, это неправильный ответ❌ Попробуйте снова
"""
    NO_WORDS_LEFT = """
Супер! Все слова закончились!
"""
    FAILURE_TRANSLATE = """
К сожалению, слово перевести не удалось.😔 Пожалуйста, введите перевод вручную📚
"""
    SHOW_DICTIONARY = """
Слова, которые вы изучаете:
{}
"""
    NO_WORDS_IN_DICT = """
Вы пока что не добавили слова!
"""
    INVALID_USER = """
Слушайте, похоже, что я вас забыл или не встречал! Давайте срочно познакомимся😊 Напиши мне /start или нажми на "Справкаℹ️"
"""

MARKUP_DEFAULT = ReplyKeyboardMarkup(resize_keyboard=True)
DEFAULT_BUTTONS = [
    KeyboardButton(Commands.ADD),
    KeyboardButton(Commands.DELETE),
    KeyboardButton(Commands.TRAIN),
    KeyboardButton(Commands.HELP),
    KeyboardButton(Commands.MY_DICTIONARY)
]
MARKUP_DEFAULT.add(*DEFAULT_BUTTONS)

def validate_target_word(target):
    """Проверяет, является ли целевое слово допустимым для записи в бд.

    Параметры:
        target (str): Слово для проверки.

    Возвращает:
        bool: True, если слово допустимо, иначе False.

    """
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz'
    allowed_chars += allowed_chars.upper() + '- '
    if not target:
        return False
    for char in target:
        if char not in allowed_chars:
            return False
    return True

def validate_translation(translate):
    """Проверяет, является ли перевод допустимым.

    Параметры:
        translate (str): Перевод для проверки.

    Возвращает:
        bool: True, если перевод допустим, иначе False.

    """
    allowed_chars = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    allowed_chars += allowed_chars.upper() + '- '
    if not translate:
        return False
    for char in translate:
        if char not in allowed_chars:
            return False
    return True

def translate_word(word):
    """Переводит английское слово на русский с помощью API Яндекс для словарей
    
    Параметры:
        word (str): Английское слово для перевода.

    Возвращает:
        str or None: Переведенное слово на русский или None, если не удалось перевести.
    
    """
    url = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
    params = {
        'key': TRANSLATE_TOKEN,
        'lang': 'en-ru',
        'text': word,
    }
    response = requests.get(url, params=params, timeout=10)
    tr_json = response.json()
    flag_found = False
    trans_word = None

    for definition in tr_json['def']:
        if not flag_found:
            for translation in definition['tr']:
                trans_word = translation['text']
                flag_found = True
                break  # первый попавшийся перевод нам подходит
    if trans_word is None:
        return None
    return trans_word.lower()

@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
    """
    Обрабатывает команды /start и /help.
    
    Отправляет приветственное сообщение пользователю. 
    Если пользователь уже зарегистрирован, отображается сообщение 
    о повторном входе. Если нет, запрашивается имя или возможность 
    остаться анонимным.
    
    Параметры:
        message (telebot.types.Message): Сообщение от пользователя, 
                                         содержащие команду.

    Ничего не возвращает в консоль

    """
    chat_id = message.chat.id
    keybord_markup = ReplyKeyboardMarkup(resize_keyboard=True)

    session = Session()
    user = list(
        session.query(Users.name, Users.tg_id).\
            select_from(Users).\
            filter(Users.tg_id == message.from_user.id).all()
        )
    session.close()

    if user:
        bot.send_message(
            chat_id,
            BotMessages.WELCOME_AGAIN,
            reply_markup=MARKUP_DEFAULT
        )
        bot.set_state(
            message.from_user.id,
            MyStates.default,  # для старых пользователей ничего не делаем
            message.chat.id
            )
    else:
        button = KeyboardButton(Commands.REFUSE_NAME_ENTER)
        keybord_markup.add(button)
        bot.send_message(
            chat_id,
            BotMessages.WELCOME,
            reply_markup=keybord_markup
        )
        bot.set_state(
            message.from_user.id,
            MyStates.waiting_for_name,  # если пользователь отказывается давать
            message.chat.id             # имя, то все равно добавляем его
        )                               # только как анонима

@bot.message_handler(
        func=lambda message:
        bot.get_state(message.from_user.id) == MyStates.waiting_for_name.name)
def set_name(message):
    """
    Обрабатывает ввод имени пользователя.
    
    Если пользователь ввел имя, оно сохраняется в базе данных. 
    Если пользователь выбрал оставаться анонимным, создается 
    запись с именем "Аноним".
    
    Параметры:
        message (telebot.types.Message): Сообщение от пользователя с именем 
                                         или командой для отказа.

    Ничего не возвращает в консоль

    """
    username = message.text
    session = Session()
    if username == Commands.REFUSE_NAME_ENTER:
        bot.reply_to(
            message,
            BotMessages.ANSWER_FOR_ANON,
            reply_markup=MARKUP_DEFAULT
        )
        user = Users(tg_id=message.from_user.id, name="Аноним")
    else:
        bot.reply_to(
            message,
            BotMessages.ANSWER_FOR_USER.format(username),
            reply_markup=MARKUP_DEFAULT
        )
        user = Users(tg_id=message.from_user.id, name=username)

    session.add(user)
    session.commit()

    session.close()
    bot.set_state(message.from_user.id, MyStates.default, message.chat.id)

@bot.message_handler(func=lambda message: message.text == Commands.ADD)
def add_word(message):
    """
    Обрабатывает команду добавления нового слова.
    
    Запрашивает у пользователя новое слово на английском языке.
    
    Параметры:
        message (telebot.types.Message): Сообщение от пользователя с 
                                         командой добавления.

    """
    chat_id = message.chat.id

    bot.send_message(chat_id, BotMessages.WAITING_NEW_WORD_ENG, reply_markup=ReplyKeyboardMarkup())
    bot.set_state(message.from_user.id, MyStates.waiting_for_target_word, chat_id)

@bot.message_handler(
        func=lambda message:
        bot.get_state(message.from_user.id) == MyStates.waiting_for_target_word.name)
def add_word_input_target(message):
    """
    Обрабатывает ввод целевого слова от пользователя.
    
    Если слово не соответствует требованиям (например, невалидное), 
    уведомляет пользователя. Если слово валидно, запрашивает 
    перевод на русский язык.

    Параметры:
        message (telebot.types.Message): Сообщение от пользователя с 
                                         целевым словом.

    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    target_word = message.text.lower()

    if not validate_target_word(target_word):
        bot.reply_to(message, BotMessages.INVALID_TARGET_WORD)
        return  # предполагается ввод слов далее
    keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_markup.add(KeyboardButton(Commands.LET_TRANSLATE))

    bot.send_message(
        chat_id,
        BotMessages.WAITING_NEW_WORD_RUS,
        reply_markup=keyboard_markup
        )
    bot.set_state(
        user_id,
        MyStates.waiting_for_translation,
        chat_id
    )
    with bot.retrieve_data(user_id, chat_id) as data:
        data['target_word'] = target_word

@bot.message_handler(
        func=lambda message:
        bot.get_state(message.from_user.id) == MyStates.waiting_for_translation.name)
def add_word_input_translation(message):
    """
    Обработчик для получения перевода слова от пользователя.
    Сохраняет целевое слово и его перевод в базе данных.
    
    Параметры:
        message (telebot.types.Message): Объект сообщения от пользователя.

    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    translation = message.text
    with bot.retrieve_data(user_id, chat_id) as data:
        target_word = data['target_word']

    if translation == Commands.LET_TRANSLATE:
        translation = translate_word(target_word)
        if translation is None:
            bot.send_message(chat_id, BotMessages.FAILURE_TRANSLATE)
            return
    translation = translation.lower()
    if not validate_translation(translation):
        bot.reply_to(message, BotMessages.INVALID_TRASLATION)
        return  # предполагается ввод слов далее

    session = Session()

    user_query = session.query(Users).\
            filter(Users.tg_id == message.from_user.id).all()
    if len(list(user_query)) > 0:
        user = user_query[0]

        word_pair = Words(target=target_word, translation=translation)
        vocabulary_pair = Vocabulary(user=user, word=word_pair)

        session.add_all([word_pair, vocabulary_pair])
        session.commit()
        session.close()
    else:
        bot.send_message(
            chat_id,
            BotMessages.INVALID_USER,
            reply_markup=MARKUP_DEFAULT
        )
        bot.set_state(user_id, MyStates.default, chat_id)
        session.close()
        return

    bot.send_message(
        message.chat.id,
        BotMessages.WORD_SUCCESS_ADDED.format(target_word, translation),
        reply_markup=MARKUP_DEFAULT
    )
    bot.set_state(user_id, MyStates.default, chat_id)

@bot.message_handler(func=lambda message: message.text == Commands.DELETE)
def delete_word(message):
    """
    Обработчик для начала процесса удаления слова.
    Запрашивает у пользователя слово для удаления.
    
    Параметры:
        message (telebot.types.Message): Объект сообщения от пользователя.
    
    """
    chat_id = message.chat.id
    user_id = message.from_user.id

    bot.send_message(chat_id, BotMessages.WAITING_DEL_WORD_ENG)
    bot.set_state(user_id, MyStates.waiting_word_to_del, chat_id)

@bot.message_handler(
        func=lambda message:
        bot.get_state(message.from_user.id) == MyStates.waiting_word_to_del.name)
def delete_word_from_db(message):
    """
    Обработчик для удаления слова из базы данных.
    Проверяет, существует ли слово, и, если да, удаляет его.
    
    Параметры:
        message (telebot.types.Message): Объект сообщения от пользователя.

    """
    word_to_del = message.text.lower()
    chat_id = message.chat.id
    user_id = message.from_user.id

    session = Session()
    word_query = session.query(Vocabulary.id, Words.id).select_from(Words).\
        join(Vocabulary, Vocabulary.word_id == Words.id).\
        join(Users, Users.id == Vocabulary.user_id).\
            filter(Users.tg_id == user_id).\
            filter(or_(Words.target == word_to_del, Words.translation == word_to_del))

    if len(list(word_query)) > 0:
        voc_id, words_id = word_query[0]
        session.query(Vocabulary).filter(Vocabulary.id == voc_id).delete()
        session.query(Words).filter(Words.id == words_id).delete()
        session.commit()
        bot.send_message(
            chat_id,
            BotMessages.SUCCESS_DELETE_WORD,
            reply_markup=MARKUP_DEFAULT
        )
    else:
        bot.send_message(
            chat_id,
            BotMessages.FAILURE_DELETE_WORD,
            reply_markup=MARKUP_DEFAULT
        )
        session.close()
        return
    session.close()
    bot.set_state(user_id, MyStates.default, chat_id)

@bot.message_handler(func=lambda message: message.text == Commands.TRAIN)
def train_words(message):
    """
    Обработчик для начала режима тренировки слов.
    Запрашивает подтверждение у пользователя.
    
    Параметры:
        message (telebot.types.Message): Объект сообщения от пользователя.

    """
    keyboard_markup = ReplyKeyboardMarkup(resize_keyboard=True)

    keyboard_markup.add(KeyboardButton(Commands.YES), KeyboardButton(Commands.NO))
    chat_id = message.chat.id
    user_id = message.from_user.id

    bot.send_message(chat_id, BotMessages.TRAINING_MODE, reply_markup=keyboard_markup)
    bot.set_state(user_id, MyStates.training, chat_id)
    with bot.retrieve_data(user_id, chat_id) as data:
        data['target_word'] = None
        data['translation'] = None
        data['all_words'] = None

@bot.message_handler(
        func=lambda message:
        bot.get_state(message.from_user.id) == MyStates.training.name)
def train_mode_iteration_start(message):
    """
    Обработчик для начала итерации тренировки слов.
    Выполняет проверку ответа пользователя и предоставляет новые слова для тренировки.
    
    Параметры:
        message (telebot.types.Message): Объект сообщения от пользователя.

    """
    answer = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id

    if answer == Commands.NO or answer == Commands.STOP_TRAINING:
        bot.send_message(chat_id, BotMessages.STOP_TRAINING, reply_markup=MARKUP_DEFAULT)
        bot.set_state(user_id, MyStates.default, chat_id)
        return

    with bot.retrieve_data(user_id, chat_id) as data:
        if data['all_words'] is not None:
            all_words = data['all_words']
        else:
            session = Session()
            all_words = get_words_list(session, user_id)
            session.close()

    if len(all_words) < 4:
        bot.send_message(chat_id, BotMessages.NO_WORDS_LEFT, reply_markup=MARKUP_DEFAULT)
        bot.set_state(user_id, MyStates.default, chat_id)
        return

    shuffle(all_words)
    others = all_words[-4:]
    target_word, translation = others[-1]
    shuffle(others)

    keyboard_markup = ReplyKeyboardMarkup()
    for _, transl in others:
        keyboard_markup.add(transl)
    keyboard_markup.add(Commands.STOP_TRAINING, *DEFAULT_BUTTONS)

    bot.send_message(
        chat_id,
        BotMessages.TRAINING_MODE_ITERATION.format(target_word),
        reply_markup=keyboard_markup
    )
    bot.set_state(user_id, MyStates.training_check, chat_id)
    with bot.retrieve_data(user_id, chat_id) as data:
        data['target_word'] = target_word
        data['translation'] = translation
        data['all_words'] = all_words[:-1]

@bot.message_handler(
        func=lambda message:
        bot.get_state(message.from_user.id) == MyStates.training_check.name)
def train_mode_iteration_end(message):
    """
    Обрабатывает завершение итерации режима тренировки для языкового перевода.
    Функция проверяет, хочет ли пользователь остановить тренировку, 
    или правильный ли его ответ. Затем отправляет соответствующий ответ 
    и перезапускает процесс тренировки.

    Аргументы:
        message (telebot.types.Message): Объект сообщения, содержащий 
                                         информацию о сообщении пользователя.

    """
    user_id = message.from_user.id
    chat_id = message.chat.id

    with bot.retrieve_data(user_id, chat_id) as data:
        translation = data['translation']

    if message.text == Commands.STOP_TRAINING:
        train_mode_iteration_start(message)
        return

    if translation == message.text:
        bot.send_message(chat_id, BotMessages.CORRECT_ANSWER)
        bot.set_state(user_id, MyStates.training, chat_id)
        train_mode_iteration_start(message)
    else:
        bot.send_message(chat_id, BotMessages.INCORRECT_ANSWER)
        return

@bot.message_handler(func=lambda message: message.text == Commands.HELP)
def show_help_info(message):
    """
    Отображает справочную информацию для пользователя.

    Аргументы:
        message (telebot.types.Message): Объект сообщения, содержащий 
                                         запрос пользователя о помощи.

    Функция отправляет приветственное сообщение с указанием направлений 
    и вариантов для пользователя.
    """
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == Commands.MY_DICTIONARY)
def show_dictionary(message):
    """
    Показывает словарь пользователя с сохраненными словами и их переводами.
    Функция выполняет запрос к базе данных для получения сохранённых слов 
    пользователя, формируя их в строку для отображения. Если слова не найдены, 
    уведомляет пользователя.

    Аргументы:
        message (telebot.types.Message): Объект сообщения, содержащий запрос 
                                         пользователя на просмотр словаря.

    """
    chat_id = message.chat.id
    user_id = message.from_user.id

    session = Session()

    dict_query = session.query(Words.target, Words.translation).select_from(Words).\
        join(Vocabulary, Vocabulary.word_id == Words.id).\
        join(Users, Users.id == Vocabulary.user_id).\
            filter(or_(Users.tg_id == user_id, Users.tg_id == 0))
    dict_list = list(dict_query)

    if len(dict_list) > 0:
        dict_str = "\n".join([" - ".join(i) for i in dict_list])
        bot.send_message(
            chat_id,
            BotMessages.SHOW_DICTIONARY.format(dict_str),
            reply_markup=MARKUP_DEFAULT
        )
    else:
        bot.send_message(
            chat_id,
            BotMessages.NO_WORDS_IN_DICT,
            reply_markup=MARKUP_DEFAULT
        )

    session.close()

if __name__ == '__main__':
    print("Bot is currently running...")
    bot.polling()
