import unittest
from main import VkBot, group_access_token

import vk_api


class TestVKinder(unittest.TestCase):

    def setUp(self):
        session = vk_api.VkApi(token=group_access_token)
        self.op_se = session.get_api()
        self.q = 'Олег Подрядов'
        self.user_id = 23225635
        self.offset = 0
        self.city = 7159
        self.dating_user_id = 23225635

    # Проверка что указанный id соответствует ФИ пользователя ВК
    def test_get_user_info(self):
        self.assertEqual(VkBot.get_user_name(self), 'Олег Подрядов')

    # Проверка что указанный город соответствует id города ВК
    def test_get_city(self):
        self.assertEqual(VkBot.get_city(self, 'Миасс'), 7159)
        self.assertEqual(VkBot.get_city(self, 'Москва'), 1)
        self.assertEqual(VkBot.get_city(self, 'Санкт-Петербург'), 2)
        self.assertEqual(VkBot.get_city(self, 'НесуществующийГород'), 0)

    # Проверка соответствия ТОП-3 фотографий пользователя ВК
    def test_get_top_photos(self):
        self.assertEqual(VkBot.get_top_photos(self), 'photo23225635_433831591,photo23225635_456240920,'
                                                     'photo23225635_457243195')


if __name__ == '__main__':
    unittest.main()
