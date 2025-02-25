from playwright.sync_api import sync_playwright, Playwright
import sqlite3
import os
import threading
import queue
import random

data = []


def run(playwright: Playwright, unit):
    global product_counter
    chromium = playwright.chromium
    browser = chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://www.vendr.com/")

    # reject cookies
    if page.locator("button#onetrust-reject-all-handler"):
        page.click("button#onetrust-reject-all-handler")
    else:
        # scroll to force load elements
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    # find the category link by main category name
    # i'll use page.goto instead of .click() to avoid switching tabs
    category_link = page.locator(f'text={unit}').locator("..")
    page.goto("https://www.vendr.com" + category_link.get_attribute('href'))
    page.wait_for_load_state('networkidle')

    # main loop
    subcategories = page.locator("//h2[contains(@class, 'rt-Heading rt-r-size-3 _cardTitle_160ph_9')]").all()

    # to avoid stale elements, looping over indexes of elements, not elements themselves
    for s in range(len(subcategories)):
        category_name = subcategories[s].text_content()
        div = subcategories[s].locator("xpath=ancestor::div[@class='rt-reset rt-BaseCard rt-Card rt-r-size-2 sm:rt-r-size-3 rt-variant-surface']")
        products = div.locator("span.rt-Text.rt-r-size-2.rt-truncate").all()

        # intermediate list to store product data, to keep elements from going stale
        product_info = []
        for p in range(len(products)):
            product_name = products[p].text_content()
            product_link = products[p].locator("xpath=ancestor::a").get_attribute('href')
            product_info.append((product_name, product_link))

        # products loop
        for name, link in product_info:
            # start new dictionary for each new product
            local_data = {}
            response = page.goto("https://www.vendr.com" + link)

            if response and response.status == 404:
                print(f"{link} had 404-ed")
                print(f"{name} not done.")
                page.go_back()
                page.reload()
                continue

            # detect network error and retry once
            if response and not response.ok:
                page.wait_for_timeout(random.randint(2000, 4000))
                response = page.reload()
                if not response.ok:
                    print(f"{name} in {unit} not done")
                    continue

            # clean data and write into local dictionary
            local_data["category"] = unit
            local_data["subcategory"] = category_name
            local_data["product_name"] = name

            prices = page.locator("span.v-fw-600.v-fs-12").all()
            price_min = prices[0].text_content() if prices else '0'
            price_max = prices[1].text_content() if len(prices) > 1 else '0'
            price_med = page.locator('span.v-fw-700.v-fs-24')
            price_median = price_med.text_content() if price_med.count() > 0 else '0'

            local_data["price_min"] = clean_number(price_min)
            local_data["price_max"] = clean_number(price_max)
            local_data["price_median"] = clean_number(price_median)

            descr = page.locator("p.rt-Text")
            description = descr.first.text_content() if descr.count() > 0 else None
            local_data["description"] = description

            print(f"{name} done.")
            page.go_back()

            # waiting randomly to avoid being kicked out
            page.wait_for_timeout(random.randint(1000, 3000))
            data.append(local_data)
            with locking_count:
                product_counter += 1
    browser.close()
    return data


# utility function to remove '$' and commas from prices
def clean_number(number: str) -> int:
    number = (number.replace(',', '')).lstrip('$')
    return int(number)


def setup_database():
    # using sqlite3 for automation and simplicity
    db_path = 'myshop.db'

    # skip if database exists
    if os.path.exists(db_path):
        print("Database exists.")
        return

    conn = sqlite3.connect('myshop.db')
    cursor = conn.cursor()
    # creating table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS goods (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   category TEXT,
                   subcategory TEXT,
                   product_name TEXT,
                   price_min INTEGER,
                   price_max INTEGER,
                   price_median INTEGER,
                   description TEXT
                   );
                   """)
    print("Database created")

    conn.commit()
    conn.close()
    return


def save_data():
    conn = sqlite3.connect('myshop.db')
    cursor = conn.cursor()

    while True:
        data = db_queue.get()
        if data is None:
            break

        cursor.executemany('''INSERT INTO goods
                   (category,
                    subcategory,
                    product_name,
                    price_min,
                    price_max,
                    price_median,
                    description)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   [tuple(data.values())])
        conn.commit()
    conn.close()
    return


def verify_data_in_db():
    conn = sqlite3.connect('myshop.db')
    cursor = conn.cursor()

    cursor.execute('''SELECT COUNT(*) FROM goods;''')
    number_of_goods = cursor.fetchone()
    conn.close()
    print(f"Number of products in database: {number_of_goods[0]}.")
    print(f"Number of scraped products: {product_counter}.")
    return


main_categories = ['IT Infrastructure',
                   'Data Analytics & Management', 'DevOps']

# creating tasks queue for scraping tasks
task_queue = queue.Queue()
for category in main_categories:
    task_queue.put(category)

# add a dedicated queue and thread to save data to the database
db_queue = queue.Queue()

product_counter = 0
locking_count = threading.Lock()


# main threading function
def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        # proceed with the scraping
        with sync_playwright() as playwright:
            run(playwright, task)
        task_queue.task_done()


def main():
    # create 3 + 1 threads
    num_of_threads = len(main_categories)
    threads = []

    # distribute the tasks among threads and start
    for i in range(num_of_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    task_queue.join()

    # now each dictionary in a list would be a batch to populate db in batches
    for batch in data:
        db_queue.put(batch)
    db_thread = threading.Thread(target=save_data)
    db_thread.start()

    # wait for tasks to finish and stop workers by adding None to the queue
    for i in range(num_of_threads):
        task_queue.put(None)

    db_queue.put(None)

    # exit scraping threads
    for thread in threads:
        thread.join()

    # exit db thread
    db_thread.join()

    return


if __name__ == '__main__':
    setup_database()
    main()
    verify_data_in_db()
