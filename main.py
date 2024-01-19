#@spectralai

import telebot
from telebot import types
import json
from datetime import datetime, time
from bg import keep_alive
from datetime import datetime, timedelta

bot = telebot.TeleBot('TOKEN')

polling = False


# Загрузка данных администратора
def load_admin_data():
  try:
    with open('admin.json', 'r') as file:
      admin_data = json.load(file)
    return admin_data
  except FileNotFoundError:
    return {}


# Сохранение данных администратора
def save_admin_data(admin_id, chat_id, vote_delays):
  admin_data = {'admin_id': admin_id, 'chat_id': chat_id, 'vote_delays': {}}
  with open('admin.json', 'w') as file:
    json.dump(admin_data, file)


# Создание голосования
def create_polling(chat_id):
  options = [
      '[1] Я буду!', '[2] Меня не будет!', '[3] Буду, но опоздаю!',
      '[4] Отсутсвую по рапорту.', '[5] Отсутвую по болезни.'
  ]
  keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2,
                                               resize_keyboard=True)
  keyboard.add(*options)
  message = bot.send_message(chat_id=chat_id,
                             text='Кто сегодня будет?',
                             reply_markup=keyboard)
  return message.message_id


def update_polling(chat_id, message_id):
  try:
    options = [
        '[1] Я буду!', '[2] Меня не будет!', '[3] Буду, но опоздаю!',
        '[4] Отсутсвую по рапорту.', '[5] Отсутвую по болезни.'
    ]
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2,
                                                 resize_keyboard=True)
    keyboard.add(*options)
    bot.edit_message_text(chat_id=chat_id,
                          message_id=message_id,
                          text='Кто сегодня будет?',
                          reply_markup=keyboard)
  except telebot.apihelper.ApiTelegramException as e:
    if e.result_json[
        'description'] == 'Bad Request: message to edit not found':
      print('The message to edit was not found.')
    else:
      print('An error occurred while editing the message:', e)


@bot.message_handler(commands=['start'])
def menu_poll(message):
  options = ['Support', 'Connection Status', 'Начать принимать оповещения']
  bot.send_message(message.chat.id,
                   "Здравствуйте, Товарищ! \nЧем могу быть полезен?",
                   reply_markup=types.ReplyKeyboardMarkup(
                       row_width=2, resize_keyboard=True).add(*options))


# Обработчик команды /start_polling
@bot.message_handler(commands=['start_polling'])
def start_polling_handler(message):
  admin_data = load_admin_data()
  global polling

  if not admin_data:
    bot.reply_to(
        message,
        'Администратор не установлен. Обратитесь к боту с командой /admin.')
    return

  if polling:
    bot.reply_to(message, 'Голосование уже запущенно!!')
    return

  if not polling:
    polling = not polling

    poll_chat_id = message.chat.id
    message_id = create_polling(poll_chat_id)

    # Сохраняем данные голосования
    poll_data = {'message_id': message_id, 'results': {}}
    with open('poll_data.json', 'w') as file:
      json.dump(poll_data, file)


# Сбор информации из голосования
@bot.message_handler(
    func=lambda message: message.text.startswith('/collect_votes'))
def collect_votes_handler(message):
  admin_data = load_admin_data()
  global polling

  if not admin_data:
    bot.reply_to(
        message,
        'Администратор не установлен. Обратитесь к боту с командой /admin.')
    return

  admin_id = admin_data['admin_id']
  chat_id = admin_data['chat_id']

  # Загрузка данных голосования
  with open('poll_data.json', 'r') as file:
    poll_data = json.load(file)

  message_id = poll_data['message_id']
  results = poll_data['results']

  # Проверяем, все ли пользователи проголосовали
  if len(results) == 0:
    bot.reply_to(message, 'Нет результатов голосования.')
    return

  # Отправка информации администратору
  result_message = '\n'.join(
      [f'> {vote}' for user_id, vote in results.items()])
  bot.send_message(chat_id=chat_id, text=result_message)
  bot.reply_to(message, '@' + result_message)
  vote = ''
  polling = not polling


# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def message_handler(message):
  admin_data = load_admin_data()

  if not admin_data:
    bot.reply_to(
        message,
        'Администратор не установлен. Обратитесь к боту с командой /admin.')
    return

  elif message.text == 'Support':
    bot.reply_to(
        message,
        'Да, конечно! Однако лично я не могу вам помочь, т.к я просто алгоритм, но вы можете обратиться к @slide36 - Администратор.'
    )

  elif message.text == 'Connection Status':
    bot.reply_to(message, 'Подключение подтверждено!')

  elif message.text == 'Начать принимать оповещения':
    admin_id = message.from_user.id
    chat_id = message.chat.id
    global vote_delays
    save_admin_data(admin_id, chat_id, vote_delays)
    bot.reply_to(message, 'Вы установили ID чата с администратором.')
  else:
    admin_id = admin_data['admin_id']
    chat_id = admin_data['chat_id']
    vote_delays = admin_data['vote_delays']

    # Обработка голосов пользователя
    with open('poll_data.json', 'r') as file:
      poll_data = json.load(file)

    message_id = poll_data.get('message_id')
    results = poll_data.get('results', {})

    if message.reply_to_message and message.reply_to_message.message_id == message_id:
      user_id = message.from_user.id
      first_name = message.from_user.first_name
      last_name = message.from_user.last_name
      vote = ''

      # Проверяем, есть ли задержка для данного пользователя
      if user_id in vote_delays:
        delay_expiration = vote_delays[user_id]
        if datetime.now() < delay_expiration:
          bot.reply_to(
              message,
              'Вы уже проголосовали. Повторное голосование будет доступно после истечения задержки.'
          )
          return

      if '[1]' in message.text:
        vote = f'{first_name} {last_name}: Я буду!'
      elif '[2]' in message.text:
        vote = f'{first_name} {last_name}: Меня не будет!'
      elif '[3]' in message.text:
        vote = f'{first_name} {last_name}: Буду, но опоздаю!'
      elif '[4]' in message.text:
        vote = f'{first_name} {last_name}: Отсутсвую по рапорту.'
      elif '[5]' in message.text:
        vote = f'{first_name} {last_name}: Отсутвую по болезни.'

      if vote:
        results[user_id] = vote
        with open('poll_data.json', 'w') as file:
          json.dump(poll_data, file)

        bot.reply_to(message,
                     text=f'{first_name} {last_name}: Ваш голос учтен.')

        # Добавляем задержку на переголосование для данного пользователя (10 сек)
        vote_delays[user_id] = datetime.now() + timedelta(seconds=10)
        admin_data['vote_delays'] = vote_delays
        save_admin_data(admin_id, chat_id, vote_delays)

        # Fix: Check if the message ID is valid before updating the polling
        if message_id:
          update_polling(chat_id, message_id)


keep_alive()
bot.polling()
