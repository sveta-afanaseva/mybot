"""
1) Реализуйте в боте команду /wordcount которая считает слова в присланной фразе. 
Например на запрос /wordcount Привет как дела бот должен ответить: 3 слова. 
Не забудьте:
Добавить проверки на пустую строку
Как можно обмануть бота, какие еще проверки нужны?

2) Реализуйте в боте команду, которая отвечает на вопрос “Когда ближайшее полнолуние?” 
Например /next_full_moon 2019-01-01. 
Чтобы узнать, когда ближайшее полнолуние, используйте ephem.next_full_moon(ДАТА)

3) Научите бота играть в города. 
Правила такие - внутри бота есть список городов, 
пользователь пишет /cities Москва и если в списке такой город есть, 
бот отвечает городом на букву "а" - "Альметьевск, ваш ход". 
Оба города должны удаляться из списка.
Помните, с ботом могут играть несколько пользователей одновременно

"""
import logging
from datetime import datetime, date
from copy import deepcopy

import ephem
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import settings


logging.basicConfig(
    format="%(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log",
)

with open("cities.txt", "r", encoding="utf-8") as f:
    cities_list = f.read().lower().split()


cities = {letter: [] for letter in list(map(chr, range(1072, 1104)))}
for city in cities_list:
    cities[city[0]].append(city)


class UserContext:
    def __init__(self) -> None:
        self.cities = deepcopy(cities)
        self.used_cities = set()
        self.last_letter = None


users = {}  # база с пользователями


def greet_user(update, context):
    update.message.reply_text(f"Привет, {update.message.chat.first_name}!")


def talk_to_me(update, context):
    user_text = update.message.text
    update.message.reply_text(user_text)


def get_constellation(update, context):
    planet = update.message.text.strip().lower().split()[-1]
    planet_obj = None

    if planet in ["sun", "солнце"]:
        planet_obj = ephem.Sun()
    if planet in ["moon", "луна"]:
        planet_obj = ephem.Moon()
    if planet in ["mercury", "меркурий"]:
        planet_obj = ephem.Mercury()
    if planet in ["venus", "венера"]:
        planet_obj = ephem.Venus()
    if planet in ["earth", "земля"]:
        update.message.reply_text("Земля не находится в созвездии")
        return
    if planet in ["mars", "марс"]:
        planet_obj = ephem.Mars()
    if planet in ["jupiter", "юпитер"]:
        planet_obj = ephem.Jupiter()
    if planet in ["saturn", "сатурн"]:
        planet_obj = ephem.Saturn()
    if planet in ["uranus", "уран"]:
        planet_obj = ephem.Uranus()
    if planet in ["neptune", "нептун"]:
        planet_obj = ephem.Neptune()
    if planet in ["pluto", "плутон"]:
        planet_obj = ephem.Pluto()

    if planet_obj is None:
        update.message.reply_text("Планета не введена либо я не знаю такой планеты")
    else:
        planet_obj.compute()
        constellation = ephem.constellation(planet_obj)
        update.message.reply_text(
            f"{planet.capitalize()} сегодня находится в созвездии {constellation[1]}"
        )


def count_words(update, context):
    sentence = update.message.text.lower()
    alphabet = (
        list(map(chr, range(97, 123)))
        + list(map(chr, range(1072, 1104)))
        + list(chr(1105))
    )
    for letter in sentence:
        if letter not in alphabet:
            sentence = sentence.replace(letter, " ")
    words_in_sentence = sentence.split()
    if len(words_in_sentence) == 1:
        update.message.reply_text("Я не смог найти ни одного слова")
    else:
        update.message.reply_text(f"В предложении слов: {len(words_in_sentence) - 1}")


def next_full_moon(update, context):
    user_text = update.message.text.strip().lower().split()
    if len(user_text) == 1:
        moon_date = date.today()
    else:
        moon_date = user_text[-1]
        try:
            moon_date = datetime.strptime(moon_date, "%Y-%m-%d")
        except ValueError:
            update.message.reply_text("Введите дату в формате YYYY-MM-DD")
            return
    next_moon_date = ephem.next_full_moon(moon_date)
    update.message.reply_text(
        "Следующее полнолуние будет "
        + next_moon_date.datetime().strftime("%d.%m.%Y %H:%M")
    )


def play_cities(update, context):
    id = update.message.from_user.id
    if id not in users:
        users[id] = UserContext()

    user_context = users[id]

    user_city = update.message.text.lower().split()[-1]
    if (
        user_context.last_letter is not None
        and user_city[0] != user_context.last_letter
    ):
        update.message.reply_text(f"Тебе на букву {user_context.last_letter.upper()}")
        return
    if user_city not in cities_list:
        update.message.reply_text("В игре участвуют только города России")
    elif user_city in user_context.used_cities:
        update.message.reply_text("Этот город уже был")
    else:
        letter = user_city[-1]
        user_context.used_cities.add(user_city)
        user_context.cities[user_city[0]].remove(user_city)
        if user_context.cities[letter]:
            update.message.reply_text(
                f"{user_context.cities[letter][-1].capitalize()}, ваш ход"
            )
            user_context.last_letter = user_context.cities[letter][-1][-1]
            user_context.used_cities.add(cities[letter].pop())
        else:
            update.message.reply_text(
                "Поздравляю! Ты выиграл! Я больше не знаю городов"
            )


def main():
    mybot = Updater(settings.API_KEY, use_context=True)

    dp = mybot.dispatcher
    dp.add_handler(CommandHandler("start", greet_user))
    dp.add_handler(CommandHandler("planet", get_constellation))
    dp.add_handler(CommandHandler("wordcount", count_words))
    dp.add_handler(CommandHandler("next_full_moon", next_full_moon))
    dp.add_handler(CommandHandler("cities", play_cities))
    dp.add_handler(MessageHandler(Filters.text, talk_to_me))

    mybot.start_polling()
    mybot.idle()


if __name__ == "__main__":
    main()
