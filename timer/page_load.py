import asyncio
import logging
import os
import random
import time
from datetime import datetime as dt
from pathlib import Path

# from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from telebot import TeleBot

from timer.constants import (ADDRESS, ALERT_ROBOT, CLIENT_IDS,
                             CREATE_REPORTS_MODEL, DATE_FORMAT, INSERT_REPORT,
                             LIMIT_FOR_ALLERT, REDUCTION, REPEAT, STATUS_CODES,
                             TABLE_NAME, TIME_FORMAT, TIMEOUT_PAGE,
                             TIMEOUT_REQUESTS)
from timer.decorators import connection_db
from timer.logging_config import setup_logging

setup_logging()

citilink_bot = TeleBot(os.getenv('CITILINK_TOKEN_TELEGRAM'))


def send_bot_message(
    url: str,
    status_code: int,
    load_time: float,
    screenshot: str
) -> None:
    """Функция отправки сообщений в телеграм."""

    # robot = CRY_ROBOT if page == 'main' else WAIT_ROBOT

    if status_code == 200:
        if load_time > LIMIT_FOR_ALLERT:
            try:
                for id in CLIENT_IDS:
                    # with open(robot, 'rb') as photo:
                    #     citilink_bot.send_sticker(id, photo)
                    citilink_bot.send_message(
                        chat_id=id,
                        text='Время ожидания ответа от сервера при загрузке '
                        f'страницы - {url} превысило критический '
                        f'максимум -  {load_time} сек!'
                        f'\nСкирншот страницы - {screenshot}'
                    )
                    logging.info(f'Сообщение отправлено пользователю {id}')
            except Exception as e:
                logging.error(f'Пользователь {id} недоступен: {e}')
    else:
        try:
            for id in CLIENT_IDS:
                with open(ALERT_ROBOT, 'rb') as photo:
                    citilink_bot.send_sticker(id, photo)
                citilink_bot.send_message(
                    chat_id=id,
                    text=f'При запросе на страницу - {url} сервер '
                    f'вернул код ответа: {status_code}. '
                    'Это значит: '
                    f'{STATUS_CODES.get(status_code, "Неизвестно")}'
                )
                logging.info(f'Сообщение отправлено пользователю {id}')
        except Exception as e:
            logging.error(f'Пользователь {id} недоступен: {e}')


async def make_dir(output_file, file_name):
    """Функция создает директорию и возваращает путь до файла."""
    folder = Path('media') / Path(output_file.split('_')[0])
    file_path = folder / file_name
    folder.mkdir(parents=True, exist_ok=True)
    return file_path


async def save_html(page, html_file_path):
    """Функция для сохранения html-файла."""
    try:
        html = await page.content()
    except Exception as error:
        logging.warning(
            'Редкая ошибка JS-скрипт начал какую-то '
            'навигацию не в тайминг: %s',
            error
        )
        await page.wait_for_timeout(1000)
        html = await page.content()

    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    logging.info('HTML сохранён → %s', html_file_path)


async def save_screenshot(page, png_file_path):
    """Функция для сохранения скриншота."""
    # await page.wait_for_timeout(TIMEOUT_SCREENSHOT)
    await page.screenshot(path=png_file_path, full_page=True)
    logging.info('Скриншот сохранён → %s', png_file_path)


async def human_actions(page):
    """Функция имитирующая поведение человека."""
    await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
    await asyncio.sleep(random.uniform(0.5, 2))
    scroll_amount = random.randint(100, 800)
    await page.mouse.wheel(0, scroll_amount)
    await asyncio.sleep(random.uniform(0.5, 2))


@connection_db
async def measure_main_page_load_time(url: str, output_file: str, cursor=None):
    # ua = UserAgent()
    async with async_playwright() as p:
        attempt = 0
        repeat_times_list = []

        cursor.execute('SHOW TABLES')
        tables_list = [table[0] for table in cursor.fetchall()]

        date_str = dt.now().strftime(DATE_FORMAT)
        time_str = dt.now().strftime(TIME_FORMAT)

        while attempt < REPEAT:

            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-ipc-flooding-protection",
                    "--disable-renderer-backgrounding",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-background-timer-throttling",
                    "--disable-client-side-phishing-detection",
                    "--disable-popup-blocking",
                    "--disable-hang-monitor",
                    "--disable-sync",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-default-apps",
                    "--disable-extensions",
                    "--disable-translate",
                    "--disable-component-extensions-with-background-pages",
                ]
            )

            # user_agent = ua.random
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'

            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'cache-control': 'max-age=0',
                'priority': 'u=0, i',
                'referer': 'https://www.google.com/',
                'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': user_agent,
            }

            context = await browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True,
                bypass_csp=True,
                ignore_https_errors=True,
            )

            await context.set_extra_http_headers(headers)
            page = await context.new_page()
            await page.add_init_script("""
                delete Object.getPrototypeOf(navigator).webdriver;
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ru-RU', 'ru', 'en-US', 'en'],
                });
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                });
            """)
            await human_actions(page)
            logging.info('Начало загрузки страницы %s', output_file)

            attempt += 1
            response = None
            hour_str = time_str.split(':')[0]
            png_file = f'{output_file}_{date_str}_{hour_str}.png'
            html_file = f'{output_file}.html'

            try:
                start_total = time.perf_counter()
                response = await page.goto(
                    url,
                    wait_until='load',
                    timeout=TIMEOUT_PAGE
                )
                # await asyncio.sleep(60)
                load_time = round(time.perf_counter() - start_total, 2)
                await human_actions(page)
                logging.info('Загрузка  завершена: %s с', round(load_time, 2))

            except Exception as error:
                logging.error(
                    'Страница %s не загрузилась за %s секунд: %s',
                    output_file,
                    TIMEOUT_PAGE / REDUCTION,
                    error
                )
                load_time = round(time.perf_counter() - start_total, 2)

            finally:
                png_file_path = await make_dir(output_file, png_file)
                html_file_path = await make_dir(output_file, html_file)
                await save_html(page, html_file_path)
                await save_screenshot(page, png_file_path)
                await context.close()
                await browser.close()

            logging.info(
                '\nПопытка %s/%s'
                '\nОБЩЕЕ ВРЕМЯ ЗАГРУЗКИ %s: %s с',
                attempt,
                REPEAT,
                output_file,
                load_time
            )
            repeat_times_list.append(load_time)
            await asyncio.sleep(TIMEOUT_REQUESTS)

        avg_time = round(sum(repeat_times_list) / len(repeat_times_list), 2)
        logging.info(
            '\nСреднее время загрузки страницы %s за %s попыток - %s',
            output_file,
            REPEAT,
            avg_time
        )

        page_name = output_file.split('_')[1]
        status_code = response.status if response else 0
        screenshot = f'{ADDRESS}{output_file.split('_')[0]}/{png_file}'
        if 'citilink' in output_file:
            send_bot_message(url, status_code, avg_time, screenshot)

        if TABLE_NAME in tables_list:
            logging.info('Таблица %s найдена в базе', TABLE_NAME)
        else:
            create_table_query = CREATE_REPORTS_MODEL.format(
                table_name=TABLE_NAME
            )
            cursor.execute(create_table_query)
            logging.info('Таблица %s успешно создана', TABLE_NAME)

        query = INSERT_REPORT.format(table_name=TABLE_NAME)
        params = [(
            date_str,
            time_str,
            url,
            page_name,
            avg_time,
            screenshot
        )]
        cursor.executemany(query, params)
        logging.info('Данные сохранены')
