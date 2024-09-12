import telebot
import config
import text_boxes
import db_methods as dbm
import logging
import time

logging.basicConfig(level=logging.INFO, filename='/home/bot/{}.log'.format(int(time.time())),
                    filemode="w", format="%(asctime)s %(levelname)s %(message)s")

logging.debug("A DEBUG Message")
logging.info("An INFO")
logging.warning("A WARNING")
logging.error("An ERROR")
logging.critical("A message of CRITICAL severity")


bot = telebot.TeleBot(config.bot_token, parse_mode=None)


@bot.message_handler(commands=['start'])
def start(message):
    try:
        logging.info(f'{message.chat.id} START:COMMAND')
        if message.chat.id not in config.admin_list:
            if not dbm.check_person(message.chat.id, message.chat.username):
                logging.info(f'{message.chat.id} START:CONFIRMATION1')
                button = telebot.types.InlineKeyboardButton(text='Ознакомлен', callback_data='ready_to_start_1')
                keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
                keyboard.add(button)
                bot.send_photo(message.chat.id, photo=text_boxes.hello_pic[0])
                bot.send_message(message.chat.id, text_boxes.hello1, reply_markup=keyboard)
            else:
                logging.info(f'{message.chat.id} START:GOTOMAIN')
                main_menu(message.chat.id)
        else:
            if dbm.get_max_gid() == 0:
                logging.info(f'{message.chat.id} START:ADMIN:NOONE')
                bot.send_message(message.chat.id, 'Пока никто не зарегистрировался =(',
                                 reply_markup=text_boxes.start_keyboard)

            else:
                logging.info(f'{message.chat.id} START:ADMIN:GOTOMAIN')
                main_menu(message.chat.id)
    except Exception as e:
        logging.error(f'{message.chat.id} START {e}')
        print('\nstart {}'.format(message.chat.id))
        print(e)
        bot.send_message(message.chat.id, text_boxes.except_text)
        main_menu(message.chat.id)


@bot.callback_query_handler(func=lambda c: True)
def inline(c):
    try:
        if c.data == 'ready_to_start_1':
            logging.info(f'{c.message.chat.id} INLINE:CONFIRMATION2')
            button = telebot.types.InlineKeyboardButton(text='Ознакомлен', callback_data='ready_to_start_2')
            keyboard = telebot.types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(button)
            bot.send_photo(c.message.chat.id, photo=text_boxes.hello_pic[1])
            bot.delete_message(c.message.chat.id, c.message.message_id)
            bot.send_message(c.message.chat.id, text_boxes.hello2, reply_markup=keyboard)
        if c.data == 'ready_to_start_2':
            logging.info(f'{c.message.chat.id} INLINE:GOTOREGISTRATION')
            bot.edit_message_text('Давай заполним анкету', c.message.chat.id, c.message.message_id)
            enter_info(None, c.message.chat.id, -1)
    except Exception as e:
        logging.error(f'{c.message.chat.id} INLINE {e}')
        print('inline {}'.format(c.message.chat.id))
        print(e)
        bot.send_message(c.message.chat.id, text_boxes.except_text)
        main_menu(c.message.chat.id)


def enter_info(msg, chat_id, step):
    try:
        if step == -1:
            msg = bot.send_message(chat_id, text_boxes.text[step+1])
            bot.register_next_step_handler(msg, enter_info, chat_id, step+1)
        else:
            logging.info(f'{msg.chat.id} ENTERINFO:STEP{step + 1}')
            logging.info(f'{msg.chat.id} ENTERINFO:TEXT {msg.text}')
            dbm.remember_info(msg, chat_id, step)
            if step == 16:
                logging.info(f'{msg.chat.id} ENTERINFO:ENDREGISTRATION')
                dbm.set_registered(chat_id)
                bot.send_message(chat_id, '🎉')
                bot.send_message(chat_id, 'Поздравлю, теперь твоя команда участвует в экоквест-игре «Мой лось»🥳🥳🥳')
                main_menu(chat_id)
            else:
                msg = bot.send_message(chat_id, text_boxes.text[step + 1])
                bot.register_next_step_handler(msg, enter_info, chat_id, step + 1)
    except Exception as e:
        logging.error(f'{msg.chat.id} ENTERINFO {e}')
        print('\nenter_info {}'.format(msg.chat.id))
        print(e)
        bot.send_message(msg.chat.id, text_boxes.except_text)
        main_menu(msg.chat.id)


def main_menu(chat_id):
    logging.info(f'{chat_id} MAIN')
    if chat_id not in config.admin_list:
        bot.send_message(chat_id, text_boxes.registration_pre, reply_markup=text_boxes.pre_main_menu_keyboard)
    else:
        info = dbm.admin_get_all()
        text = ''
        for item in info:
            exclaim = '❗️' if item['pending'] else ''
            text += '{}{}. {}\nКапитан: {}\n\n'.format(exclaim, item['gid'], item['team'], item['leader'])
        text += 'Наберите номер команды для более подробной информации'
        keyboard = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        keyboard.add(*[telebot.types.KeyboardButton(str(i)) for i in range(1, len(info)+1)])
        keyboard.add(telebot.types.KeyboardButton(text_boxes.cancel))
        msg = bot.send_message(chat_id, text, reply_markup=keyboard)
        bot.register_next_step_handler(msg, check_team)


def check_team(message):
    try:
        logging.info(f'{message.chat.id} CHECK')
        if message.text.isdigit() and 0 < int(message.text) <= len(dbm.admin_get_all()):
            team_info = dbm.get_team_members(message.text)
            uid = dbm.get_chat_id_by_id(team_info['l'][0])
            team = dbm.get_team(uid)
            name = team_info['l'][1]
            gnum = dbm.get_gnum(uid)
            phone = team_info['l'][2]
            email = team_info['l'][3]
            mentor = team_info['m'][1]
            mentor_phone = team_info['m'][2]
            mentor_email = team_info['m'][3]
            members = []
            phones = []
            emails = []
            for i in range(3):
                members.append(team_info['g'][i][1])
                phones.append(team_info['g'][i][2])
                emails.append(team_info['g'][i][3])
            stage = dbm.get_stage(uid)
            pending = 'Да❗️' if dbm.get_pending(uid) else 'Нет'
            extra = len(dbm.get_upload(uid, True))
            text = text_boxes.admin_full_info.format(message.text, team, name, gnum, phone, email,
                                                     mentor, mentor_phone, mentor_email,
                                                     members[0], phones[0], emails[0],
                                                     members[1], phones[1], emails[1],
                                                     members[2], phones[2], emails[2],
                                                     stage, pending, extra)
            print(text)
            if dbm.get_username(uid) == ' ':
                msg = bot.send_message(message.chat.id, text, reply_markup=text_boxes.cancel_keyboard)
            else:
                name = '[{}](t.me/{})'.format(team_info['l'][1], dbm.get_username(uid))
                text += '\nСсылка: {}'.format(name)
                msg = bot.send_message(message.chat.id, text, parse_mode='Markdown',
                                       link_preview_options=telebot.types.LinkPreviewOptions(True),
                                       reply_markup=text_boxes.cancel_keyboard)
            logging.info(f'{message.chat.id} CHECK:GIVELIST')
            bot.register_next_step_handler(msg, check_task, uid)
        else:
            logging.info(f'{message.chat.id} CHECK:WRONG')
            main_menu(message.chat.id)
    except Exception as e:
        logging.error(f'{message.chat.id} CHECK {e}')
        print('\ncheck_team {}'.format(message.chat.id))
        print(e)
        bot.send_message(message.chat.id, text_boxes.except_text)
        main_menu(message.chat.id)


def check_task(message, uid):
    try:
        logging.info(f'{message.chat.id} CHECKTASK')
        main_menu(message.chat.id)
    except check_task as e:
        logging.error(f'{message.chat.id} CHECKTASK {e}')
        print('\ncheck_task {}'.format(message.chat.id))
        print(e)
        bot.send_message(message.chat.id, text_boxes.except_text)
        main_menu(message.chat.id)


@bot.message_handler(func=lambda message: message.chat.id not in config.admin_list, content_types=['text'])
def user_interface(message):
    try:
        if not dbm.check_person(message.chat.id, message.chat.username):
            logging.info(f'{message.chat.id} INTERFACE:BACKTOSTART')
            start(message)
        else:
            logging.info(f'{message.chat.id} INTERFACE')
            dbm.set_username(message.chat.id, message.chat.username)
            logging.info(f'{message.chat.id} INTERFACE:USERNAME {message.chat.username}')
            if message.text == text_boxes.main_menu_buttons[1][0]:
                show_info(message.chat.id)
            else:
                main_menu(message.chat.id)
    except check_task as e:
        logging.error(f'{message.chat.id} INTERFACE {e}')
        print('\nuser_interface {}'.format(message.chat.id))
        print(e)
        bot.send_message(message.chat.id, text_boxes.except_text)
        main_menu(message.chat.id)


def show_info(chat_id):
    try:
        logging.info(f'{chat_id} SHOWINFO')
        members = dbm.get_team_members(dbm.get_gid(chat_id))
        mentor = members['m'][1]
        mentor_phone = members['m'][2]
        mentor_email = members['m'][3]
        group = [name[1] for name in members['g']]
        phones = [name[2] for name in members['g']]
        emails = [name[3] for name in members['g']]
        text = text_boxes.full_info.format(dbm.get_name(chat_id), dbm.get_gnum(chat_id), dbm.get_phone(chat_id),
                                           dbm.get_email(chat_id), dbm.get_team(chat_id),
                                           mentor, mentor_phone, mentor_email,
                                           group[0], phones[0], emails[0],
                                           group[1], phones[1], emails[1],
                                           group[2], phones[2], emails[2])
        msg = bot.send_message(chat_id, text, reply_markup=text_boxes.change_info_keyboard)
        bot.register_next_step_handler(msg, change_info_choice)
    except check_task as e:
        logging.error(f'{chat_id} SHOWINFO {e}')
        print('\nshow_info {}'.format(chat_id))
        print(e)
        bot.send_message(chat_id, text_boxes.except_text)
        main_menu(chat_id)


def change_info_choice(message):
    try:
        logging.info(f'{message.chat.id} CHANGECHOICE {message.text}')
        if message.text == text_boxes.cancel:
            main_menu(message.chat.id)
        else:
            msg = bot.send_message(message.chat.id, 'Введите новое значение', reply_markup=text_boxes.cancel_keyboard)
            bot.register_next_step_handler(msg, change_info, find_index(message.text))
    except check_task as e:
        logging.error(f'{message.chat.id} CHANGECHOICE {e}')
        print('\nchange_info_choice {}'.format(message.chat.id))
        print(e)
        bot.send_message(message.chat.id, text_boxes.except_text)
        main_menu(message.chat.id)


def find_index(foo):
    for i in text_boxes.change_info_buttons:
        if foo in i:
            return text_boxes.change_info_buttons.index(i), i.index(foo)


def change_info(message, choice):
    try:
        logging.info(f'{message.chat.id} CHANGE {message.text}')
        if message.text == text_boxes.cancel:
            main_menu(message.chat.id)
        else:
            if choice[0] == 0:
                if choice[1] == 0:
                    dbm.set_name(message.chat.id, message.text)
                elif choice[1] == 1:
                    dbm.set_gnum(message.chat.id, message.text)
                elif choice[1] == 2:
                    dbm.set_phone(message.chat.id, message.text)
            elif choice[0] == 1:
                if choice[1] == 0:
                    dbm.set_email(message.chat.id, message.text)
                elif choice[1] == 1:
                    dbm.set_team(message.chat.id, message.text)
            elif choice[0] == 2:
                gid = dbm.get_gid(message.chat.id)
                uid = dbm.get_team_members(gid)['m'][0]
                if choice[1] == 0:
                    dbm.set_team_member(uid, message.text)
                elif choice[1] == 1:
                    dbm.set_team_member(uid, message.text, type='phone')
                elif choice[1] == 2:
                    dbm.set_team_member(uid, message.text, type='email')
            elif choice[0] == 3:
                gid = dbm.get_gid(message.chat.id)
                uid = dbm.get_team_members(gid)['g'][0][0]
                if choice[1] == 0:
                    dbm.set_team_member(uid, message.text)
                elif choice[1] == 1:
                    dbm.set_team_member(uid, message.text, type='phone')
                elif choice[1] == 2:
                    dbm.set_team_member(uid, message.text, type='email')
            elif choice[0] == 4:
                gid = dbm.get_gid(message.chat.id)
                uid = dbm.get_team_members(gid)['g'][1][0]
                if choice[1] == 0:
                    dbm.set_team_member(uid, message.text)
                elif choice[1] == 1:
                    dbm.set_team_member(uid, message.text, type='phone')
                elif choice[1] == 2:
                    dbm.set_team_member(uid, message.text, type='email')
            elif choice[0] == 5:
                gid = dbm.get_gid(message.chat.id)
                uid = dbm.get_team_members(gid)['g'][2][0]
                if choice[1] == 0:
                    dbm.set_team_member(uid, message.text)
                elif choice[1] == 1:
                    dbm.set_team_member(uid, message.text, type='phone')
                elif choice[1] == 2:
                    dbm.set_team_member(uid, message.text, type='email')
            bot.send_message(message.chat.id, "Успешно изменено")
            main_menu(message.chat.id)
    except check_task as e:
        logging.error(f'{message.chat.id} CHANGE {e}')
        print('\nchange_info {}'.format(message.chat.id))
        print(e)
        bot.send_message(message.chat.id, text_boxes.except_text)
        main_menu(message.chat.id)


if __name__ == "__main__":
    bot.infinity_polling()
