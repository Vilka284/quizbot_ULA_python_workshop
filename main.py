"""
Телеграм бот для опитувань.
ULA Python workshop
"""

import logging
import random
from datetime import datetime
from logging import info

import telegram
import yaml  # pyyaml
from telegram.ext import Updater, CommandHandler, MessageHandler, PicklePersistence

# Для нашого воркшопу можемо використовувати і print(),
# але логер дає більше можливостей у відстеженні роботи бота
logging.basicConfig(
    # filename='conversations.log',
    format='%(asctime)s %(levelname)-7s %(name)s %(message)s')
logging.getLogger().setLevel('INFO')

# Перед початком роботи потрібно створити бота через BotFather та вставити у змінну TOKEN секретний ключ
TOKEN = "TOKEN HERE"

# Список користувачів, що можуть проходити квест
# def is_user_authorized(user, msg):
#     authorized_users = ['crinitus_vulpi']
#     if user.username in authorized_users:
#         return True
#     msg.bot.send_message(msg.chat_id,
#                          text=f'Тобі не дозволено проходити тест! Звернись до адміністратора.',
#                          reply_markup=telegram.ReplyKeyboardRemove())
#     return False


DURATION = 5


class Question:

    def __init__(self, qid, question, answers):
        self.qid = qid
        self.text = question
        self.answers = {}
        self.correct = None
        for a in answers:
            letter_choice = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[len(self.answers)]
            if isinstance(a, str):
                self.answers[letter_choice] = a
            elif isinstance(a, dict) and len(a) == 1 and 'correct' in a and self.correct is None:
                self.answers[letter_choice] = a['correct']
                self.correct = letter_choice
            else:
                raise ValueError(f'Incorrect answers in question {qid}: {answers}')


with open("questions.yaml", "r") as file:
    yaml_file = yaml.safe_load(file)

# Створюємо питання
QUESTIONS = {q['id']: Question(q['id'], q['q'], q['a']) for q in yaml_file}


def start(update, context):
    """Функція для команди /start"""

    msg = update.message
    user = msg.from_user
    info(f'Користувач виконав команду /start: {user.id} @{user.username} "{user.first_name} {user.last_name}"')

    # Дозвіл тільки переліченим користувачам проходити тест
    # if not is_user_authorized(user, msg):
    #     return

    if 'username' not in context.user_data:
        context.user_data['username'] = user.username

    msg.bot.send_message(msg.chat_id,
                         text=f'Починаємо тест. У тебе буде {DURATION} хвилин на {len(QUESTIONS)} питань. Приготувались?',
                         reply_markup=telegram.ReplyKeyboardMarkup([['Почати тест']]))


def common_message(update, context):
    """Функція для текстових повідомлень"""

    msg = update.message
    user = msg.from_user
    info(f'Отримано повідомлення від {user.id} @{user.username}: {msg.text}')

    # Дозвіл тільки переліченим користувачам проходити тест
    # if not is_user_authorized(user, msg):
    #     return

    if 'quiz' not in context.user_data:
        info(f'Користувач {user.id} @{user.username} почав тест')
        context.user_data['quiz'] = {}
        context.user_data['quiz']['answers'] = {}
        start_time = datetime.now()
        context.user_data['quiz']['start_time'] = start_time

        msg.bot.send_message(msg.chat_id,
                             text=f'Тест почато о {start_time}',
                             reply_markup=telegram.ReplyKeyboardRemove())
    else:
        # Зберігаємо відповідь
        current_question = context.user_data['quiz']['current_qid']
        context.user_data['quiz']['answers'][current_question] = msg.text

    # Ставимо запитання
    questions_left = set(QUESTIONS) - set(context.user_data['quiz']['answers'])
    if len(questions_left) > 0:
        # Обираємо випадкове питання
        question = QUESTIONS[random.sample(questions_left, 1)[0]]
        msg.bot.send_message(msg.chat_id,
                             text=f'{question.text}\n' +
                                  '\n'.join(f'{aid}. {text}' for aid, text in sorted(question.answers.items())),
                             reply_markup=telegram.ReplyKeyboardMarkup([[aid for aid in sorted(question.answers)]]))

        context.user_data['quiz']['current_qid'] = question.qid

    else:
        context.user_data['quiz']['current_qid'] = None

        # Рахуємо чи користувач вклався у виділений час
        end_time = datetime.now()
        if not context.user_data['quiz'].get('end_time'):
            context.user_data['quiz']['end_time'] = end_time
        test_time = context.user_data['quiz']['end_time'] - context.user_data['quiz']['start_time']
        test_time_minutes = test_time.seconds / 60

        if test_time_minutes > DURATION:
            msg.bot.send_message(msg.chat_id,
                                 text=f'Ти не встиг пройти тест вчасно :(',
                                 reply_markup=telegram.ReplyKeyboardRemove())
            return

        msg.bot.send_message(msg.chat_id,
                             text=f'Тест пройдено!',
                             reply_markup=telegram.ReplyKeyboardRemove())


def main():
    # Зберігаємо контекст бота, щоб при перезапуску зчитувати його
    storage = PicklePersistence(filename='data.pickle')
    updater = Updater(token=TOKEN, persistence=storage, use_context=True)
    dp = updater.dispatcher

    # Прив'язуємо функції відповідно до контенту повідомлень
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(None, common_message))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
