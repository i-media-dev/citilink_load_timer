import asyncio

from timer.constants import SHOPS
from timer.decorators import time_of_script
from timer.page_load import measure_main_page_load_time


@time_of_script
async def main():
    tasks = []

    for shop in SHOPS:
        output_file_main = f'{shop}_main'
        output_file_cart = f'{shop}_cart'
        url_main, url_cart = SHOPS[shop]

        tasks.append(measure_main_page_load_time(
            url_main, output_file_main))
        tasks.append(measure_main_page_load_time(
            url_cart, output_file_cart))

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
