import telebot
import sqlite3
import threading
import random
from telebot import types
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from threading import Thread
from settings import TG_TOKEN


# Создать экземпляр бота
bot = telebot.TeleBot(TG_TOKEN)

# Id проектных менеджеров
managersid = [1059219533, 5149703369, 498357388]

lock = threading.Lock()

# база данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, message TEXT, user_id TEXT, date TEXT, time TEXT)''')
conn.commit()

def db_table_val(username: str, message: str, user_id: str, date: str, time: str):
	cursor.execute('INSERT INTO users (username, message, user_id, date, time) VALUES (?, ?, ?, ?, ?)', (str(username), str(message), str(user_id), str(date), str(time)))
	conn.commit()



# Основное меню
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Проголосовать')
    markup.add(btn1)
    bot.send_message(message.chat.id, "Добро пожаловать в бот для отслеживания уровня энергии проектной команды!", reply_markup=markup)

# Статистика всех
@bot.message_handler(commands=['statsall'])
def statsall(message):
    if message.chat.id not in managersid:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.", reply_markup=markup)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Дня')
        btn2 = types.KeyboardButton('Недели')
        btn3 = types.KeyboardButton('Общая')
        btn4 = types.KeyboardButton('База данных')
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id, "Выберите промежуток:", reply_markup=markup)

# Статистика отдельного участника
@bot.message_handler(commands=['statsmember'])
def statsmember(message):
    markup = types.ReplyKeyboardRemove()
    if message.chat.id not in managersid:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.", reply_markup=markup)
    else:
        sqlite_select_query2 = """SELECT DISTINCT username from users"""
        my_cursor2 = cursor.execute(sqlite_select_query2)
        global members
        members = []
        for row4 in my_cursor2:
            members.append(row4[0])
        send = bot.send_message(message.chat.id, "Введите имя пользователя участника без @", reply_markup=markup)
        bot.register_next_step_handler(send, statsmember_end)
        
def statsmember_end(message):
    if message.text in members:
        statsmember = cursor.execute('SELECT message FROM users WHERE username=?', (message.text, ))
        votes3 = []
        for row5 in statsmember:
            value3 = row5[0]
            votes3.append(int(value3[:value3.index('%')]))
        sum_votes = sum(votes3)
        votes_avg = sum_votes/len(votes3)
        bot.send_message(message.chat.id, f"Вот средний процент энергии этого участника - {int(votes_avg)}" + "%")
    else:
        bot.send_message(message.chat.id, "Такого пользователя нет в базе.")


    
# Статистика за всё время    
@bot.message_handler(regexp='Общая')
def general(message):
    if message.chat.id not in managersid:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "О чём вы?", reply_markup=markup)
    else:
        sqlite_select_query1 = """SELECT message from users"""
        my_cursor1 = cursor.execute(sqlite_select_query1)
        votes = []
        for row1 in my_cursor1:
            value = row1[0]
            votes.append(int(value[:value.index('%')]))
        sum_votes = sum(votes)
        try:
            votes_avg = sum_votes/len(votes)
            bot.send_message(message.chat.id, f"Вот средний процент энергии участников за всё время - {int(votes_avg)}" + "%")
        except Exception as e:
            bot.send_message(message.chat.id, f"Ошибка при работе с базой! - {e}")
    

# Статистика за неделю
@bot.message_handler(regexp='Недели')
def weekly(message):
    if message.chat.id not in managersid:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "О чём вы?", reply_markup=markup)
    else:
        past_date = datetime.today() - timedelta(days=7)
        cur_date = datetime.today()
        current_date = str(cur_date.date())
        pastable_date = str(past_date.date())
        info = cursor.execute('SELECT * FROM users WHERE date=?', (pastable_date, )).fetchone()
        #Если запрос вернул 0 строк, то...
        if info is None: 
            bot.send_message(message.chat.id, "Недостаточно данных за этот период!")
        else:
            votes_weekly = cursor.execute('SELECT message FROM users WHERE date BETWEEN ? and ?', (str(pastable_date), str(current_date)))
            votes1 = []
            for row2 in votes_weekly:
                value1 = row2[0]
                votes1.append(int(value1[:value1.index('%')]))
            sum_votes_week = sum(votes1)
            votes_avg_week = sum_votes_week/len(votes1)
            bot.send_message(message.chat.id, f"Вот средний процент энергии участников за неделю - {int(votes_avg_week)}" + "%")

# Статистика за день            
@bot.message_handler(regexp='Дня')        
def daily(message):
    if message.chat.id not in managersid:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "О чём вы?", reply_markup=markup)
    else:
        cur_date = datetime.today()
        current_date = str(cur_date.date())
        try:
            lock.acquire(True)
            info = cursor.execute('SELECT * FROM users WHERE date=?', (current_date, )).fetchone()
        finally:
            lock.release()
        #Если запрос вернул 0 строк, то...
        if info is None: 
            bot.send_message(message.chat.id, "Недостаточно данных за этот период!")
        else:
            votes_daily = cursor.execute('SELECT message FROM users WHERE date=?', (str(current_date), ))
            votes2 = []
            for row3 in votes_daily:
                value2 = row3[0]
                votes2.append(int(value2[:value2.index('%')]))
            sum_votes_day = sum(votes2)
            votes_avg_day = sum_votes_day/len(votes2)
            global recomend_votes
            recomend_votes = votes_avg_day
            bot.send_message(message.chat.id, f"Вот средний процент энергии участников за день - {int(votes_avg_day)}" + "%")

# Рекомендации по управлению для менеджера
@bot.message_handler(commands=['recommendations'])
def recommendations(message):
    markup = types.ReplyKeyboardRemove()
    if message.chat.id not in managersid:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.", reply_markup=markup)
    else:
        try:
            if recomend_votes >= 50:
                bot.send_message(message.chat.id, "Рекомендация: Поддерживайте высокий уровень энергии команды, предоставляя им возможности для роста и развития, поощряя командную работу и сотрудничество, и признавая их достижения.", reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "Рекомендация: Проанализируйте причины низкой энергии и разработайте стратегии для их устранения. Рассмотрите возможность организации командных мероприятий, проведения мозгового штурма или пересмотра рабочих процессов для повышения мотивации и вовлеченности.", reply_markup=markup)
        except Exception:
            bot.send_message(message.chat.id, "Произошла ошибка, сначала просмотрите статистику дня.", reply_markup=markup)

# Отправить менеджеру базу данных
@bot.message_handler(regexp='База данных')
def db(message):
    markup = types.ReplyKeyboardRemove()
    if message.chat.id not in managersid:
        bot.send_message(message.chat.id, "У вас нет прав доступа к этой команде.", reply_markup=markup)
    else:
        # Путь к базе данных
        bot.send_document(message.chat.id, open(r"C:/Users/alexr160921/Desktop/lost city/VS CODE/users.db"), reply_markup=markup)



# Рассылка
def mailing():
    sqlite_select_query = """SELECT DISTINCT user_id from users"""
    my_cursor = cursor.execute(sqlite_select_query)
    for row in my_cursor:
        usid = row[0]
        try:
            bot.send_message(usid, "Время голосовать")
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {usid}: {e}")




#scheduler = BlockingScheduler()
#scheduler.add_job(mailing, "interval", seconds=7)

scheduler = BlockingScheduler(timezone="Europe/Moscow") # You need to add a timezone, otherwise it will give you a warning
scheduler.add_job(mailing, "cron", hour=7) # Runs every day at 8:00



# Голосование
@bot.message_handler(regexp='Проголосовать')
def vote(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup1 = types.ReplyKeyboardRemove()
    btn1 = types.KeyboardButton('0%')
    btn2 = types.KeyboardButton('20%')
    btn3 = types.KeyboardButton('50%')
    btn4 = types.KeyboardButton('80%')
    btn5 = types.KeyboardButton('100%')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    datime = datetime.fromtimestamp(message.date)
    usid = message.from_user.id
    da = datime.date()
    user_id = usid
    date = str(da)
    info = cursor.execute('SELECT * FROM users WHERE user_id=? and date=?', (user_id, date, ))
    if info.fetchone() is None: 
        send_energy = bot.send_message(message.chat.id, "Выберите ваш текущий уровень энергии🔋:", reply_markup=markup)
        bot.register_next_step_handler(send_energy, energy)
    else:
        bot.send_message(message.chat.id, "Вы уже голосовали сегодня!😊", reply_markup=markup1)  
    

def energy(message):
    if message.text == "0%" or '20%' or '50%' or '80%' or '100%':
        us_name = message.from_user.username
        mess = message.text
        usid = message.from_user.id
        datime = datetime.fromtimestamp(message.date)
        da = datime.date()
        ti = datime.time()
        db_table_val(username=us_name, message=mess, user_id=usid, date=da, time=ti)
        if message.text == '0%':
            markup1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup1.add('Продолжить', 'Пропустить')
            msg = bot.send_message(message.chat.id, "Кажется все идёт совсем не так, как хотелось бы. Давайте обсудим ваши переживания и разберёмся в причинах", reply_markup=markup1)
            bot.register_next_step_handler(msg, process_first_question)
        elif message.text == '20%':
            markup1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup1.add('Советы при жизненных трудностях', 'Мотивационные личности', 'Пропустить')
            msg = bot.send_message(message.chat.id, "Вы неважно себя чувствуете? Выберете то, что могло бы помочь вам прямо сейчас.", reply_markup=markup1)
            bot.register_next_step_handler(msg, process_first_question)
        elif message.text == '50%':
            markup1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup1.add('Совет при выгорании', 'Краткая добрая история', 'Пропустить')
            msg = bot.send_message(message.chat.id, "Вас что-то беспокоит? Выберите, что вам может помочь почувствовать себя лучше", reply_markup=markup1)
            bot.register_next_step_handler(msg, process_first_question)
        elif message.text == '80%':
            markup1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup1.add('Краткая добрая история', 'Жизненный совет', 'Пропустить')
            msg = bot.send_message(message.chat.id, "Твоя улыбка и хорошее настроение делают нашу команду сплоченнее. Спасибо за это", reply_markup=markup1)
            bot.register_next_step_handler(msg, process_first_question)
        elif message.text == '100%':
            markup1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup1.add('Анекдот', 'Жизненный совет', 'Обратная связь', 'Пропустить')
            msg = bot.send_message(message.chat.id, "Ты сегодня просто сияешь! Твое хорошее настроение поднимет настроение всем :D", reply_markup=markup1)
            bot.register_next_step_handler(msg, process_first_question)


    else:
        bot.send_message(message.chat.id, "Я вас не понял.)")

def process_first_question(message):
    if message.text == 'Продолжить':
        msg = bot.send_message(message.chat.id, "Как вы себя чувствуете на работе в последнее время? (Это поможет понять общий уровень стресса и удовлетворенности.)")
        bot.register_next_step_handler(msg, process_second_question)
    elif message.text == 'Советы при жизненных трудностях':
        bot.send_message(message.chat.id, "Разрешите себе не идеальность\nНе стремитесь к идеалу — он недостижим. Позвольте себе ошибаться и учитесь на этих ошибках.\nПересмотрите свои приоритеты Если работа становится источником чрезмерного стресса, возможно, стоит пересмотреть свои приоритеты. Найдите баланс между работой и личной жизнью.\nНайдите новые источники вдохновения Познавайте новые области, читайте книги, смотрите вдохновляющие видео или посещайте семинары. Новые идеи и знания могут вдохновить вас на новые достижения.\nНайдите причины Задумайтесь о том, что именно вызывает у вас трудности или выгорание. Это может быть перегрузка, недостаток мотивации или проблемы в команде. Понимание причин поможет вам найти решения.")
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")
    elif message.text == 'Мотивационные личности':
        bot.send_message(message.chat.id, """
        Опра Уинфри
        Опра Уинфри сталкивалась с многими трудностями в жизни, включая бедность и переживание эмоционального выгорания на ранних стадиях своей карьеры. Сначала она работала на телевидении и сталкивалась с предвзятостью, но не сдалась. В конечном итоге она стала одной из самых влиятельных женщин в мире и создала собственную телевизионную империю.
        Роберт Бернс (Burns)
        Работающий в сфере бизнеса, Роберт Бернс прошел через банкротство и потерю бизнеса. Он смог восстановить свою карьеру и начать новые проекты, пришел к значительному успеху и стал успешным предпринимателем.""")
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")
    elif message.text == 'Совет при выгорании':
        bot.send_message(message.chat.id, """План выхода из выгорания:
        1. Анализ сфер жизни и своих потребностей
        2. Отдых "ничегонеделанием"
        3. Отпуск или снижение нагрузки
        4. Прогулки на природе, медитации, творчество
        5. Массаж, плавание, дыхательные практики
        6. Маленькие перемены: новые хобби, места, еда, маршруты, запахи""")
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")
    elif message.text == 'Краткая добрая история':
        history = ["""Сегодня на обеде обратил внимание, что один из комплектовщиков (бородатый мужик ближе к 40) смотрит на планшете мультик про Губку Боба. Это очень не вязалось с общим видом и возрастом смотрящего. И я обратился к нему с вопросом: 
        — Ну как, нравится? 
        — Да так себе, — скривился, но смотрит внимательно так. 
        — А зачем смотришь? 
        — Да это я для дочки... 
        Как оказалось, у мужика дочка 7 лет. Слепая с рождения. И вот папа смотрит «Губку Боба» и потом каждый вечер рассказывает ей в виде сказок на свой лад. Уже так просмотрены «Маша и Медведь» и другие мультики. Пытался ей аудиокнижки включать, но дочке нравится, чтобы именно папа рассказывал. Мы слушали его, и у некоторых на глазах были слезы. Начальник грузчиков, высокий седой армянин, спрятал лицо в ладонях и так просидел минут 10. Было интересно наблюдать за реакцией всей толпы. Никто не сидел с безразличным видом. Всех зацепило.""", """На днях ехала в троллейбусе. Зашел молодой человек лет 20–25. Сел, целую остановку мучился, разматывая наушники со сломанной рукой. За 2 минуты до моей остановки, когда троллейбус затормозил перед светофором, я подошла к нему и размотала их. Пока разматывала, молодой человек сидел и улыбался. Вышла — коленки все тряслись. Первый раз не побоялась сделать добро.""", """ Еду в метро, глаза от линз красные, слезятся. Боль жуткая, а снять некуда. Всю дорогу справа у дверей стоял парень весь в белом и наблюдал, на конечной вышел за мной. Он купил пионов у какой-то бабушки у метро, догнал меня у остановки и, вручая, сказал: «Не надо плакать, всё будет хорошо», - и ушёл. Даже свою остановку пропустил. """]
        history_mes = random.choice(history)
        bot.send_message(message.chat.id, history_mes)
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")
    elif message.text == 'Жизненный совет':
        soviet = ["""Начинайте утро с благодарности. Каждое утро выделяйте немного времени, чтобы вспомнить о трех вещах, за которые вы благодарны. Это поможет настроиться на позитивный лад.""", """Пейте достаточно воды. Соблюдайте водный баланс, начиная день со стакана воды. Это поможет вам чувствовать себя более бодрым пробудив ваш организм и включит все системы для лучшего состояния с самого утра.""", """Планируйте свой день. Каждое утро уделяйте несколько минут для составления списка задач. Это поможет организовать мысли и сделать день более продуктивным."""]
        soviet_mes = random.choice(soviet)
        bot.send_message(message.chat.id, soviet_mes)
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")
    elif message.text == 'Анекдот':
        anekdots = ["Срочно требуется опытный хакер! Резюме оставлять на рабочем столе нашего сервера.", "Британские ученые обнаружили у овощей способность к общению друг с другом. В основном это общение происходит через социальные сети.", """ Босс спрашивает у сотрудника:
        – Почему у тебя всегда опаздывают отчеты?
        Сотрудник:
        – Я стараюсь создавать ожидание!"""]
        anekdots_mes = random.choice(anekdots)
        bot.send_message(message.chat.id, anekdots_mes)
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")
    elif message.text == 'Обратная связь':
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")
        msg = bot.send_message(message.chat.id, "Поделитесь  что или кто вам нравится в коллективе и на вашем рабочем месте. Возможно, этот позитив увидят и другие!")
        bot.register_next_step_handler(msg, process_four_question)
    else:
        bot.send_message(message.chat.id, "Спасибо за голосование🙃.)")

def process_second_question(message):
    msg = bot.send_message(message.chat.id, "Что бы вы хотели изменить в своей работе или карьере? (Это может помочь выявить ваши желания и потребности.)")
    bot.register_next_step_handler(msg, process_third_question)

def process_third_question(message):
    bot.send_message(message.chat.id, "Ваши мысли и предложения обсудятся на ближайшем собрании. Спасибо вам за ответы и потраченное время, будем ждать вас завтра!")

def process_four_question(message):
    bot.send_message(message.chat.id, "Спасибо запрос отправлен!")




def schedule_checker():
    while True:
        scheduler.start()
        break
        


Thread(target=schedule_checker).start()

bot.polling(none_stop=True)