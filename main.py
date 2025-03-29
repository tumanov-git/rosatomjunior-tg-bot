import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

#ф-я для первого вопроса
def check_math_equivalence(user_text: str) -> bool:
    pattern = r'([\d\.,\+\-\*/\(\)\s]+=[\d\.,\+\-\*/\(\)\s]+)'
    match = re.search(pattern, user_text)
    if not match:
        return False
    expr = match.group(1).replace(',', '.')
    try:
        left_expr, right_expr = expr.split('=')
        left_val = eval(left_expr)
        right_val = eval(right_expr)
    except Exception:
        return False
    # Если левая и правая части равны и равны 80 (с допуском)
    return abs(left_val - right_val) < 1e-6 and abs(right_val - 80) < 1e-6

#ф-я для бана
def is_user_banned(user_id):
    try:
        with open("loxi.txt", "r", encoding="utf-8") as f:
            banned_users_info = f.readlines()
        # Проверка, если user_id есть в файле
        for line in banned_users_info:
            if str(user_id) in line:  # Проверяем, есть ли user_id в строке
                return True
    except FileNotFoundError:
        return False
    return False

#инфа всякая
API_TOKEN = '7784020444:AAFs-wBkRi0LI9PUL7ek2XOSCZ0svrO6e-o'  
ADMIN_USER_IDS = [898091017]  # Замените на свой Telegram user_id

logging.basicConfig(
    level=logging.INFO,              # Уровень логирования (INFO, DEBUG, ERROR и т.д.)
    format='%(asctime)s - %(levelname)s - %(message)s'  # Формат сообщений
)

banned_users = set()

# Загрузка запрещённых слов из файла banned_words.txt (одна строчка — одно слово)
with open("banned_words.txt", "r", encoding="utf-8") as f:
    banned_words = [line.strip().lower() for line in f if line.strip()]

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Список вопросов для квиза. Вопросы и ответы можно редактировать по необходимости.
questions = [
    {"question": "1. что показывают стрелки часов? нам нужно [РЕШЕНИЕ]", "answer": "(1,5+6.5)*10=80", "hint": "все, что ты ищешь, есть на твоем мерче. посмотри внимательнее."},
    {"question": "Сколько будет 2+2?", "answer": "4"},
    {"question": "Как называется планета, на которой мы живем?", "answer": "земля"}
]

# In-memory хранилище состояния пользователей
# Структура: { user_id: {"current_question": int, "wrong_attempts": int} }
user_states = {}

async def forward_message_to_admin(message: types.Message):
    admin_user_id = 898091017
    await bot.send_message(admin_user_id, f"Новое сообщение от пользователя {message.from_user.id} ({message.from_user.username}):\n{message.text}")


# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    if is_user_banned(message.from_user.id):
        await message.reply("поздравляю! ты забанен. больше не можешь проходить квиз. хаха")
        return
    logging.info(f"Command /start received from user {message.from_user.id}")  # Логирование
    user_states[message.from_user.id] = {
        "current_question": 0,
        "wrong_attempts": 0,
        "banned_attempts": 0  # инициализируем счетчик нарушений
    }
    welcome_text = (
        "<b>добро пожаловать в [ИГРУ]</b>\n\n"
        "ты получил этот мерч. у него есть несколько секретов.\n"
        "первый разгадаешь секреты — получишь <code>`‘Ў#B±БRСр$3br`</code>.\n\n"
        "<i>удачи!</i>"
    )
    await message.reply(welcome_text, parse_mode='HTML')
    # Отправка первого вопроса
    first_question = questions[0]["question"]
    await message.answer(first_question)

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    logging.info(f"Command /admin received from user {message.from_user.id}")  # Логирование
    if message.from_user.id not in ADMIN_USER_IDS:
        logging.info(f"User {message.from_user.id} is not an admin.")  # Логирование
        await message.reply("ты что, самый умный?")
        return

    # Создадим строку с информацией о пользователях
    user_info = "Список пользователей:\n\n"
    for user_id, state in user_states.items():
        user_info += f"ID: {user_id}, Прогресс: Вопрос {state['current_question'] + 1}, Неверных попыток: {state['wrong_attempts']}\n"
    
    # Отправляем администратору информацию
    await message.reply(user_info if user_info else "Нет данных о пользователях.", parse_mode="Markdown")

@dp.message(Command("banned"))
async def view_banned(message: types.Message):
    if message.from_user.id not in ADMIN_USER_IDS:
        await message.reply("ты что, самый умный?")
        return

    try:
        with open("loxi.txt", "r", encoding="utf-8") as f:
            banned_users_info = f.read()
    except FileNotFoundError:
        banned_users_info = "Нет забаненных пользователей."

    await message.reply(f"Список забаненных пользователей:\n{banned_users_info}")


# Основной обработчик сообщений (ответов пользователя)
@dp.message()
async def handle_answer(message: types.Message):
    await forward_message_to_admin(message)
    user_text = message.text.lower().strip()
    user_id = message.from_user.id

    # Извлечение информации о пользователе
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name or ""  # Если фамилии нет
    username = message.from_user.username or "Не задан"  # Если ника нет

    # Логирование в файл
    with open("messages_log.txt", "a", encoding="utf-8") as f:
        f.write(f"User {user_id} - {first_name} {last_name} (@{username}): {message.text}\n")
    
    # Логирование в консоль
    logging.info(f"Message from {first_name} {last_name} (@{username}, User ID: {user_id}): {message.text}")


    # Если пользователь не начал квиз командой /start
    if user_id not in user_states:
        await message.reply("тут есть команда /start")
        return

    state = user_states[user_id]
    current_index = state["current_question"]

    # Проверка на наличие запрещённых слов с использованием счетчика
    if any(banned_word in user_text for banned_word in banned_words):
        state["banned_attempts"] += 1
        if state["banned_attempts"] == 1:
            await message.reply("эй, мы тут так не говорим. это последнее предупреждение")
            return
        elif state["banned_attempts"] >= 2:
            await message.reply("ну, я предупреждал. твой контакт уже направлен @ivan_samolin")
            banned_users.add(user_id)  # Добавляем пользователя в список заблокированных
            # Записываем данные о заблокированном пользователе в файл "loxi.txt"
            with open("loxi.txt", "a", encoding="utf-8") as f:
                first_name = message.from_user.first_name
                last_name = message.from_user.last_name or ""
                username = message.from_user.username or "Не задан"
                f.write(f"{user_id} - {first_name} {last_name} (@{username})\n")
            del user_states[user_id]
            return


    # Если квиз уже завершён
    if current_index >= len(questions):
        await message.reply("ты уже завершил квиз. хочешь еще, нажми /start")
        return
    
    # Специальная проверка для первого вопроса
    if current_index == 0:
        if check_math_equivalence(user_text):
            state["current_question"] += 1
            state["wrong_attempts"] = 0  # сбрасываем счетчик неправильных попыток
            if state["current_question"] < len(questions):
                next_question = questions[state["current_question"]]["question"]
                await message.reply("отлично. отлично:\n" + next_question)
            else:
                await message.reply("Поздравляем, вы завершили квиз!")
                del user_states[user_id]
            return
        if user_text.strip() == "80":
            await message.reply("ты близок, но нам нужно [РЕШЕНИЕ].")
            return


    # Получаем правильный ответ для текущего вопроса
    correct_answer = questions[current_index]["answer"].lower().strip()
    
    if user_text == correct_answer:
        # Верный ответ: переходим к следующему вопросу
        state["current_question"] += 1
        state["wrong_attempts"] = 0  # сбрасываем счетчик неправильных попыток
        if state["current_question"] < len(questions):
            next_question = questions[state["current_question"]]["question"]
            await message.reply("Верно! Следующий вопрос:\n" + next_question)
        else:
            await message.reply("Поздравляем, вы завершили квиз!")
            # Очистка состояния пользователя после завершения квиза
            del user_states[user_id]
    else:
        # Неверный ответ: увеличиваем счетчик неправильных попыток
        state["wrong_attempts"] += 1
        if state["wrong_attempts"] == 10:
            # Получаем подсказку для текущего вопроса
            hint = questions[state["current_question"]].get("hint", "Подсказки пока нет")
            await message.reply(f"Неправильно. Подсказка: {hint}")
        


async def main():
    # Запуск бота в режиме long polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

#проверка 0.3333