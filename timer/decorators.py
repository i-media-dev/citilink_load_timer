import functools
import logging
import time
from datetime import datetime as dt

import mysql.connector

from timer.constants import DATE_FORMAT, MAX_RETRIES, TIME_DELAY, TIME_FORMAT
from timer.db_config import config
from timer.logging_config import setup_logging

setup_logging()


def time_of_script(func):
    """Декортаор для измерения времени работы всего приложения."""
    @functools.wraps(func)
    async def wrapper():
        date_str = dt.now().strftime(DATE_FORMAT)
        time_str = dt.now().strftime(TIME_FORMAT)
        run_id = str(int(time.time()))
        print(f'Функция main начала работу {date_str} в {time_str}')
        start_time = time.time()
        try:
            result = await func()
            execution_time = round(time.time() - start_time, 3)
            print(
                'Функция main завершила '
                f'работу в {dt.now().strftime(TIME_FORMAT)}.'
                f' Время выполнения - {execution_time} сек. '
                f'или {round(execution_time / 60, 2)} мин.'
            )
            logging.info('SCRIPT_FINISHED_STATUS=SUCCESS')
            logging.info('DATE=%s', date_str)
            logging.info('EXECUTION_TIME=%s сек', execution_time)
            logging.info('FUNCTION_NAME=%s', func.__name__)
            logging.info('RUN_ID=%s', run_id)
            logging.info('ENDLOGGING=1')
            return result
        except Exception as error:
            execution_time = round(time.time() - start_time, 3)
            print(
                'Функция main завершилась '
                f'с ошибкой в {dt.now().strftime(TIME_FORMAT)}. '
                f'Время выполнения - {execution_time} сек. '
                f'Ошибка: {error}'
            )
            logging.info('SCRIPT_FINISHED_STATUS=ERROR')
            logging.info('DATE=%s', date_str)
            logging.info('EXECUTION_TIME=%s сек', execution_time)
            logging.info('ERROR_TYPE=%s', type(error).__name__)
            logging.info('ERROR_MESSAGE=%s', str(error))
            logging.info('FUNCTION_NAME=%s', func.__name__)
            logging.info('RUN_ID=%s', run_id)
            logging.info('ENDLOGGING=1')
            raise
    return wrapper


def time_of_function(func):
    """
    Декоратор для измерения времени выполнения функции.

    Замеряет время выполнения декорируемой функции и логирует результат
    в секундах и минутах. Время округляется до 3 знаков после запятой
    для секунд и до 2 знаков для минут.

    Args:
        func (callable): Декорируемая функция, время выполнения которой
        нужно измерить.

    Returns:
        callable: Обёрнутая функция с добавленной функциональностью
        замера времени.
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = round(time.time() - start_time, 3)
        logging.info(
            'Функция %s завершила работу. Время выполнения - %s сек. '
            'или %s мин.',
            func.__name__,
            execution_time,
            round(execution_time / 60, 2)
        )
        return result
    return wrapper


def connection_db(func):
    """
    Декоратор для подключения к базе данных.

    Подключается к базе данных, обрабатывает ошибки в процессе подключения,
    логирует все успешные/неуспешные действия, вызывает функцию, выполняющую
    действия в базе данных и закрывает подключение.

    Args:
        func (callable): Декорируемая функция, которая выполняет
        действия с базой данных.

    Returns:
        callable: Обёрнутая функция с добавленной функциональностью
        подключения к базе данных и логирования.
    """
    async def wrapper(*args, **kwargs):
        connection = None
        cursor = None
        delay = TIME_DELAY
        max_retries = MAX_RETRIES

        for attempt in range(max_retries):
            try:
                connection = mysql.connector.connect(**config)
                cursor = connection.cursor()
                kwargs['cursor'] = cursor
                result = await func(*args, **kwargs)
                connection.commit()
                return result
            except (
                mysql.connector.errors.ConnectionTimeoutError,
                mysql.connector.errors.OperationalError
            ) as e:
                if attempt < max_retries - 1:
                    logging.warning(
                        f'Попытка {attempt + 1} не удалась, '
                        f'повтор через {delay}с: {e}'
                    )
                    time.sleep(delay)
                    continue
                else:
                    logging.error(
                        f'Все {max_retries} попыток подключения не удались'
                    )
                    raise
            except Exception as e:
                if connection:
                    connection.rollback()
                logging.error(
                    f'Ошибка в {func.__name__}: {str(e)}', exc_info=True)
                raise
            finally:
                if cursor:
                    cursor.close()
                if connection and connection.is_connected():
                    connection.close()
    return wrapper
