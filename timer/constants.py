import os

from dotenv import load_dotenv

load_dotenv()

CRY_ROBOT = 'robot/cry-robot.png'
"""Стикер плачущего робота."""

WAIT_ROBOT = 'robot/wait-robot.png'
"""Стикер ждущего робота"""

ALERT_ROBOT = 'robot/phone_error-robot.png'
"""Стикер робота для общих уведомлений."""

REDUCTION = 1000
"""Константа для перевода в секунды."""

REPEAT = 1
"""Количество загрузок страницы."""

TIMEOUT_REQUESTS = 5
"""Таймаут между запросами."""

TIMEOUT_SCREENSHOT = 1000
"""Задержка перед скрином."""

TIMEOUT_PAGE = 60000
"""Таймаут запроса к странице."""

ADDRESS = 'https://feeds.i-media.ru/scripts/citilink_load_timer/media/'
"""Путь к файлу на ftp."""

TABLE_NAME = 'citilink_loading_reports'

TIME_DELAY = 5
"""Время повторного реконнекта к дб в секундах."""

MAX_RETRIES = 5
"""Максимальное количество переподключений к бд."""

DATE_FORMAT = '%Y-%m-%d'
"""Формат даты по умолчанию."""

TIME_FORMAT = '%H:%M:%S'
"""Формат времени по умолчанию."""

SHOPS = {
    'mvideo': (
        'https://www.mvideo.ru/',
        'https://www.mvideo.ru/cart',
    ),
    'citilink': (
        'https://www.citilink.ru/',
        'https://www.citilink.ru/order/',
    ),
    # 'technopark': (
    #     'https://www.technopark.ru/',
    #     'https://www.technopark.ru/cart/',
    # ),
    # 'rbt': (
    #     'https://www.rbt.ru/',
    #     'https://www.rbt.ru/basket/',
    # ),
    # 'dns': (
    #     'https://www.dns-shop.ru/',
    #     'https://www.dns-shop.ru/cart/',
    # ),
}
"""Словарь всех сайтов с urls главной страницы и корзины."""

LIMIT_FOR_ALLERT = 2.0
"""Верхний предел ожидания ответа от сервера."""

CLIENT_IDS = (os.getenv('GROUP_ID'),)
"""Кортеж доступных id."""

STATUS_CODES = {
    0: 'Не удалось дождаться ответа от сервера (сайт лежит)',
    200: 'OK - Успешный запрос',
    201: 'Created - Ресурс создан',
    202: 'Accepted - Запрос принят, но еще не обработан',
    204: 'No Content - Нет содержимого для возврата',
    301: 'Moved Permanently - Постоянное перенаправление',
    302: 'Found - Временное перенаправление',
    304: 'Not Modified - Контент не изменился',
    400: 'Bad Request - Неверный запрос',
    401: 'Unauthorized - Требуется аутентификация',
    403: 'Forbidden - Доступ запрещен',
    404: 'Not Found - Ресурс не найден',
    405: 'Method Not Allowed - Метод не разрешен',
    408: 'Request Timeout - Таймаут запроса',
    429: 'Too Many Requests - Слишком много запросов',
    500: 'Internal Server Error - Внутренняя ошибка сервера',
    502: 'Bad Gateway - Плохой шлюз',
    503: 'Service Unavailable - Сервис недоступен',
    504: 'Gateway Timeout - Таймаут шлюза',
}
"""Словарь кодов ответов от сервера и их значения."""

CREATE_REPORTS_MODEL = '''
CREATE TABLE IF NOT EXISTS {table_name} (
    `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `date` DATE NOT NULL,
    `time` TIME NOT NULL,
    `website` VARCHAR(255) NOT NULL,
    `page_name` VARCHAR(255) NOT NULL,
    `loading_time` DECIMAL(10,2) UNSIGNED NOT NULL,
    `screenshot` VARCHAR(500) NOT NULL,
    UNIQUE KEY `unique_{table_name}_combo` (`date`, `time`, `website`)
);
'''
"""Запрос на создание таблицы бд."""

INSERT_REPORT = '''
INSERT INTO {table_name} (
    date,
    time,
    website,
    page_name,
    loading_time,
    screenshot
)
VALUES (%s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE id = id
'''
