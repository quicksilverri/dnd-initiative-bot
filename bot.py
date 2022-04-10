import telegram 
from telegram.ext import (
    Updater, 
    ConversationHandler,
    CallbackContext, 
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from telegram.update import Update
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)

import logging
import os

PORT = int(os.environ.get('PORT', 80))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

#constants
ADD_CHARACTERS, PROCESS_INITIATIVES, RUN_FIGHT = range(3)
LIST_OF_CHARACTERS, COUNTER, SORTED_LIST = range(10, 13)

TOKEN = '5111911547:AAG7bWaeQFOJoYJI6rlNpjK_LzgaGo62r8k'
HEROKU = 'https://dnd-initiative-bot.herokuapp.com/'


class Character:
    def __init__(self, name: str, initiative: int): 
        self.name = name
        self.init = initiative


def sort_initiatives(initiative_list: list):
    return sorted(initiative_list, key=lambda x: x.init, reverse=True)

def pretty_initiative(initiative_list: list):
    result = ''
    for character in initiative_list: 
        result += f'{character.name} ({str(character.init)}) \n'

    return result


def start(update: Update, context: CallbackContext):
    text = '''Привет! Этот бот умеет трекерить инициативу :З
    Жмякни кнопочку внизу, чтобы начать!'''

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text='Добавить персонажей', callback_data='add')]
        ], 
        one_time_keyboard=True
    )

    context.bot.send_message(
        text=text, 
        chat_id=update.effective_chat.id,
        reply_markup=keyboard,
    )

    logger.info('bot started')

    return ADD_CHARACTERS 


def add_characters(update: Update, context: CallbackContext):
    text = '''Введи имена персонажей и его инициативу через пробел, каждый новый персонаж с новой строки:
    Арья-Старк 10
    Голлум 39'''

    context.bot.send_message(
        text=text, 
        chat_id=update.effective_chat.id
    )

    logger.info('add_characters finished')

    return PROCESS_INITIATIVES

    
def process_initiatives(update: Update, context: CallbackContext):
    # add character into character_list
    user = context.user_data
    user[LIST_OF_CHARACTERS] = []

    character_list = update.message.text.split('\n')
    for character in character_list:
        character_name, character_initiative = character.split()
        character_item = Character(character_name, int(character_initiative))
        user[LIST_OF_CHARACTERS].append(character_item)
        logger.info(f'character {character_item.name} processed')

    initiatives = user[LIST_OF_CHARACTERS]
    nice_initiatives = sort_initiatives(initiatives)
    user[SORTED_LIST] = nice_initiatives

    text=f'''Персонажи добавлены в список инициативы!
    Персонажи в порядке инициативы:
    {pretty_initiative(nice_initiatives)}'''

    keyboard = InlineKeyboardMarkup(
        [
            # [InlineKeyboardButton(text='Добавь еще персонажа', callback_data='add_charater')], 
            [InlineKeyboardButton(text='В боевку!', callback_data='start_fight')]
        ], 
        one_time_keyboard=True
    )

    context.bot.send_message(
        text=text, 
        reply_markup=keyboard, 
        chat_id=update.effective_chat.id 
    )

    user[COUNTER] = 0

    logger.info('all characters processed')

    return RUN_FIGHT


def run_fight(update: Update, context: CallbackContext):
    user = context.user_data
    counter = user[COUNTER]
    number_of_characters = len(user[LIST_OF_CHARACTERS])
    current_round = counter // number_of_characters + 1
    current_character_number = counter % number_of_characters
    current_character = user[SORTED_LIST][current_character_number]

    text = f'''Сейчас ходит {current_character.name} ({current_character.init})!
    Текущий раунд - {current_round}'''
    
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(text='Следующий персонаж', callback_data='next')], 
            [InlineKeyboardButton(text='Закончить боевку', callback_data='end')]
        ], 
        one_time_keyboard=True 
    )

    update.callback_query.edit_message_text(
        text=text, 
        reply_markup=keyboard, 
        # chat_id=update.effective_chat.id
    )

    user[COUNTER] += 1

    logger.info(f'''current_round = {current_round}, current_character = {current_character.name}, characters = {number_of_characters}, 
    user_id = {update.effective_chat.id}''')

    return RUN_FIGHT 


def end(update: Update, context: CallbackContext): 
    text = 'Спасибо за использование бота!'

    context.bot.send_message(
        text=text, 
        chat_id=update.effective_chat.id
    )

    logger.info('bot finished')

    return ConversationHandler.END

def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher 

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start)
        ], 
        states={
            ADD_CHARACTERS: [CallbackQueryHandler(add_characters, pattern='add')],
            PROCESS_INITIATIVES: [MessageHandler(Filters.text, process_initiatives)],
            RUN_FIGHT: [
                CallbackQueryHandler(run_fight, pattern='start_fight'), 
                CallbackQueryHandler(run_fight, pattern='next'), 
                CallbackQueryHandler(end, 'end')
            ],
        }, 
        fallbacks=[
            CallbackQueryHandler(end, pattern='end'),
            CommandHandler('end', end)]
    )

    dp.add_handler(conv_handler)

    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN,
                          webhook_url=HEROKU + TOKEN)
    
    updater.idle()

if __name__ == '__main__':
    main()
