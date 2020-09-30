from vk_api.longpoll import VkLongPoll, VkEventType
from random import randrange
from messages import *
import requests
import vk_api
import re
import db

# Токен сообщества
group_access_token = 'вставьте сюда Ваш токен сообщества ВК'

# Токен пользователя
user_access_token = 'вставьте сюда Ваш токен пользователя ВК'

# Авторизуемся как сообщество
vk = vk_api.VkApi(token=group_access_token)

# Работа с сообщениями
longpoll = VkLongPoll(vk)


# Функция отправки сообщения
def write_msg(user_id, message, attachment=''):
    vk.method('messages.send', {'user_id': user_id, 'message': message,
                                'random_id': randrange(10 ** 7), 'attachment': attachment})


# Получение параметров для отправки запроса
def get_params(add_params: dict = None):
    params = {
        'access_token': user_access_token,
        'v': '5.107'
    }
    if add_params:
        params.update(add_params)
        pass
    return params


class VkBot:

    # Инициализация бота
    def __init__(self, user_id):
        self.user = db.User
        self.user_id = user_id
        self.commands = ['ПРИВЕТ', 'СТАРТ', 'ПОКА', 'ВЫВЕСТИ', 'ИЗМЕНИТЬ', 'УДАЛИТЬ', 'ПРОДОЛЖИТЬ']
        self.first_name = ''
        self.last_name = ''
        self.city = 0
        self.age_range = ''
        self.age_from = 0
        self.age_to = 0
        self.sex = 0
        self.offset = 0  # Смещение относительно первого найденного пользователя
        self.dating_user_id = 0
        self.top_photos = ''

    # Получаем имя, фамилию пользователя
    def get_user_name(self):
        response = requests.get(
            'https://api.vk.com/method/users.get',
            get_params({'user_ids': self.user_id})
        )
        for user_info in response.json()['response']:
            self.first_name = user_info['first_name']
            self.last_name = user_info['last_name']
        return self.first_name + ' ' + self.last_name

    # Отправка сообщений ботом
    def new_message(self, message):
        # Привет
        if message.upper() == self.commands[0]:
            return GREETING_MESSAGE

        # Старт
        elif message.upper() == self.commands[1]:
            return self.run()

        # Пока
        elif message.upper() == self.commands[2]:
            return GOOD_BYE_MESSAGE

        # Неизвестное боту сообщение
        else:
            return UNKNOWN_MESSAGE

    # Основной цикл поиска
    def run(self):
        self.get_user_name()
        db.create_tables()
        write_msg(self.user_id, INPUT_TOWN_MESSAGE)
        for new_event in longpoll.listen():
            if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                if self.get_city(new_event.message) == 0:
                    write_msg(self.user_id, UNKNOWN_TOWN_MESSAGE)
                else:
                    self.get_age_range()
                    self.get_sex()
                    self.user = db.User(vk_id=self.user_id, first_name=self.first_name,
                                        last_name=self.last_name, range_age=self.age_range, city=self.city)
                    db.add_user(self.user)
                    self.find_dating_user()
                    self.get_top_photos()
                    write_msg(self.user_id, f'Имя: {self.first_name}\n'
                                            f'Фамилия: {self.last_name}\nСсылка: @id{self.dating_user_id}',
                              self.top_photos)
                    return self.find_love()

    # Меню бота
    def bot_menu(self):
        """
        Вы в главном меню. Введите одну из команд:
        ВЫВЕСТИ - вывести список всех понравившихся Вам людей;
        ИЗМЕНИТЬ – изменить критерии поиска человека;
        УДАЛИТЬ – удалить человека из списка понравившихся Вам людей;
        ПРОДОЛЖИТЬ – продолжить поиск второй половинки;
        ПОКА - завершить беседу
        """
        write_msg(self.user_id, self.bot_menu.__doc__)
        while True:
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                    if new_event.message.upper() == self.commands[3]:
                        write_msg(self.user_id, DATING_USERS_LIST_MESSAGE)
                        dating_users = db.view_all(self.user_id)
                        for dating_user in dating_users:
                            write_msg(self.user_id, f'@id{dating_user}')
                        write_msg(self.user_id, self.bot_menu.__doc__)

                    # Изменить
                    elif new_event.message.upper() == self.commands[4]:
                        self.offset = 0
                        self.run()

                    # Удалить
                    elif new_event.message.upper() == self.commands[5]:
                        write_msg(self.user_id, DATING_USERS_LIST_MESSAGE)
                        dating_users = db.view_all(self.user_id)
                        for dating_user in dating_users:
                            write_msg(self.user_id, f'@id{dating_user}')
                        write_msg(self.user_id, INPUT_ID_MESSAGE)
                        self.delete_dating_user(dating_users)
                        write_msg(self.user_id, self.bot_menu.__doc__)

                    # Продолжить
                    elif new_event.message.upper() == self.commands[6]:
                        write_msg(self.user_id, CONTINUE_FIND_MESSAGE)
                        self.offset += 1
                        self.find_dating_user()
                        self.get_top_photos()
                        self.find_love()

                    # Пока
                    elif new_event.message.upper() == self.commands[2]:
                        return self.new_message(new_event.message.upper())

                    # Неизвестное боту сообщение
                    else:
                        write_msg(self.user_id, UNKNOWN_MESSAGE)

    # Удаляем понравившегося человека из БД
    def delete_dating_user(self, dating_users):
        for new_event in longpoll.listen():
            if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                if int(new_event.message) in dating_users:
                    db.delete_user(new_event.message)
                    return write_msg(self.user_id, DELETE_MESSAGE)
                elif int(new_event.message) == 0:
                    return write_msg(self.user_id, RETURN_MESSAGE)
                else:
                    write_msg(self.user_id, UNKNOWN_ID_MESSAGE)

    # Вспомогательный цикл поиска (пока не найдем нужного нам человека)
    def find_love(self):
        write_msg(self.user_id, DO_YOU_LIKE_IT_MESSAGE)
        while True:
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                    if new_event.message.lower() == 'да':
                        dating_user = db.DatingUser(vk_id=self.dating_user_id, first_name=self.first_name,
                                                    last_name=self.last_name, id_User=self.user.id)
                        db.add_user(dating_user)
                        write_msg(self.user_id, ADD_MESSAGE)
                        return self.bot_menu()
                    else:
                        write_msg(self.user_id, CONTINUE_FIND_MESSAGE)
                        self.offset += 1
                        self.find_dating_user()
                        self.get_top_photos()
                        write_msg(self.user_id, DO_YOU_LIKE_IT_MESSAGE)

    # Получаем идентификатор города
    def get_city(self, city):
        response = requests.get(
            'https://api.vk.com/method/database.getCities',
            get_params({'country_id': 1, 'count': 1, 'q': city})
        )
        if not response.json()['response']['items']:
            return 0
        else:
            for city_id in response.json()['response']['items']:
                self.city = city_id['id']
            return self.city

    # Диапазон возраста
    def get_age_range(self):
        write_msg(self.user_id, INPUT_RANGE_AGE_MESSAGE)
        for new_event in longpoll.listen():
            if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                self.age_range = re.findall(r'\d+', new_event.message)
                self.age_range = [int(i) for i in self.age_range]
                # noinspection PyBroadException
                try:
                    if len(self.age_range) == 1 and 18 <= self.age_range[0] <= 80:
                        self.age_from = self.age_range[0]
                        self.age_to = self.age_range[0]
                        return self.age_range
                    elif 18 <= self.age_range[0] < self.age_range[1] and self.age_range[0] < self.age_range[1] <= 80:
                        self.age_from = self.age_range[0]
                        self.age_to = self.age_range[1]
                        return self.age_range
                    else:
                        write_msg(self.user_id, UNKNOWN_AGE_MESSAGE)
                except:
                    write_msg(self.user_id, UNKNOWN_AGE_MESSAGE)

    # Пол
    def get_sex(self):
        write_msg(self.user_id, INPUT_SEX_MESSAGE)
        for new_event in longpoll.listen():
            if new_event.type == VkEventType.MESSAGE_NEW and new_event.to_me:
                if new_event.message.lower() == 'мужской' or new_event.message.lower() == 'м':
                    self.sex = 2
                    return self.sex
                elif new_event.message.lower() == 'женский' or new_event.message.lower() == 'ж':
                    self.sex = 1
                    return self.sex
                else:
                    write_msg(self.user_id, UNKNOWN_MESSAGE)

    # Поиск половинки (id)
    def find_dating_user(self):
        response = requests.get(
            'https://api.vk.com/method/users.search',
            get_params({'count': 1,
                        'offset': self.offset,
                        'city': self.city,
                        'country': 1,
                        'sex': self.sex,
                        'age_from': self.age_from,
                        'age_to': self.age_to,
                        'fields': 'is_closed',
                        'status': 6,  # Ищем только тех, кто в активном поиске
                        'has_photo': 1}
                       )
        )
        if response.json()['response']['items']:
            for dating_user_id in response.json()['response']['items']:
                private = dating_user_id['is_closed']
                if private:
                    self.offset += 1
                    self.find_dating_user()
                else:
                    self.dating_user_id = dating_user_id['id']
                    self.first_name = dating_user_id['first_name']
                    self.last_name = dating_user_id['last_name']
        else:
            self.offset += 1
            self.find_dating_user()

    # Получаем ТОП-3 фотографий найденного пользователя
    def get_top_photos(self):
        photos = []
        response = requests.get(
            'https://api.vk.com/method/photos.get',
            get_params({'owner_id': self.dating_user_id,
                        'album_id': -6,
                        'extended': 1,
                        'count': 255}
                       )
        )
        # noinspection PyBroadException
        try:
            sorted_response = sorted(response.json()['response']['items'],
                                     key=lambda x: x['likes']['count'], reverse=True)
            for photo_id in sorted_response:
                photos.append(f'''photo{self.dating_user_id}_{photo_id['id']}''')
            self.top_photos = ','.join(photos[:3])
            return self.top_photos
        except:
            pass


# Основной цикл
if __name__ == '__main__':
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            bot = VkBot(event.user_id)
            write_msg(event.user_id, bot.new_message(event.text))
