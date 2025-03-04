from playwright.sync_api import sync_playwright, Playwright
import multiprocessing as mp
import re


class BookScraper:
    def __init__(self, startpoint, first_page, last_page):
        self.book_counter = 0
        self.startpoint = startpoint
        self.first_page = first_page
        self.last_page = last_page
        self.start = 0
        self.end = 0

    def get_book_links(self):
        for a_try in range(0, 2):
            # this is a cryptic way of constructing the link with the given page rage
            response = self.page.goto(self.startpoint + f'catalogue/page-{self.first_page}.html')
            if response and response.status < 400:
                break
            print('Webpage isn\'t responsive, retrying...')
        else:
            print('Webpage doesn\'t respond. Stopping script.')
            return []

        # scrape all book names and links in a given page range
        book_list = self.page.locator('li.col-xs-6.col-sm-4.col-md-3.col-lg-3').all()
        books = []
        current_page = self.first_page
        while current_page <= self.last_page:
            for b in range(len(book_list)):
                li = book_list[b].locator('h3 > a')
                book_name = li.get_attribute('title') if li else None
                book_link = 'https://books.toscrape.com/catalogue/' + li.get_attribute('href') if li else None
                books.append((book_name, book_link))
            # update current page number using current link with some trimming
            current_page = int((self.page.url.rstrip('.html')).lstrip('https://books.toscrape.com/catalogue/page-'))

            # stop turning pages if ran out of pages
            if not self.turn_page():
                break
        return books

    # utility function to clean price data and cast into float
    def clean(self, price: str) -> float:
        new_price = price.strip('£')
        return float(new_price)

    # utility function to obtain the rating
    def count(self, stars):
        ratings = {'One': '1/5', 'Two': '2/5',
                   'Three': '3/5', 'Four': '4/5', 'Five': '5/5'}
        rating = (stars.split(' '))[1]
        return ratings[rating]

    # utility function to turn the amount of books in stock into integer
    def number(self, stock: str) -> int:
        numbers = r"\d+"
        match = re.search(numbers, stock)
        return int(match.group()) if match else 0

    def turn_page(self):
        pagination = self.page.locator('li.next > a')
        if pagination.count() > 0:
            pagination.click()
            return True
        return False

    def get_book_data(self, list_of_books):
        library = []
        # scrape all the required elements
        for name, link in list_of_books:
            self.page.goto(link)

            price = self.page.locator('div > div > p.price_color')
            price_clean = self.clean(price.text_content()) if price.count() > 0 else 0

            in_stock = self.page.locator("div > div > p.instock.availability")
            available = self.number(in_stock.inner_text()) if in_stock.count() > 0 else 0

            stars = self.page.locator('div > div > p.star-rating')
            rating = self.count(stars.get_attribute('class')) if stars.count() > 0 else '0/5'

            categories = self.page.locator('li.active').locator("xpath=preceding-sibling::li[1]/a")
            category_name = categories.text_content() if categories.count() > 0 else None

            img = self.page.locator('div.item.active > img')
            img_link = 'https://books.toscrape.com/' + (img.get_attribute('src')).lstrip('../..') if img.count() > 0 else None

            descr = self.page.locator('div#product_description').locator("xpath=following-sibling::p")
            description = descr.text_content() if descr.count() > 0 else None

            upc = self.page.locator('th', has_text='UPC').locator("xpath=following-sibling::td")
            upc_num = upc.text_content() if upc.count() > 0 else None

            product_type = self.page.locator('th', has_text='Product Type').locator("xpath=following-sibling::td")
            p_type = product_type.text_content() if product_type.count() > 0 else None

            reviews = self.page.locator('th', has_text='Number of reviews').locator("xpath=following-sibling::td")
            review_num = reviews.text_content() if reviews.count() > 0 else 0

            # write the elements into dictionary
            book = {'name': name,
                    'price': price_clean,
                    'category': category_name,
                    'available': available,
                    'rating': rating,
                    'img_link': img_link,
                    'description': description,
                    'UPC': upc_num,
                    'type': p_type,
                    'reviews_amount': review_num}
            library.append(book)
            self.book_counter += 1
            # break
        print(f"This Process scraped '{library[0]['name']}', '{library[-1]['name']}' and others. {self.book_counter} books in total.\n")
        return True

    def run(self):
        # exit when queue runs out of tasks
        if None in {self.startpoint, self.first_page, self.last_page}:
            self.stop()
            return
        # initializing playwright in run, as in __init__ it can't get pickled
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()

        book_links = self.get_book_links()
        self.get_book_data(book_links)
        self.stop()

    def stop(self):
        self.browser.close()
        self.playwright.stop()
        return


class ProcessManager:
    def __init__(self, startpoint, tasks, num_of_processes=1):
        self.num_of_processes = num_of_processes
        self.processes_list = []
        self.queue = mp.Queue()
        self.tasks = tasks
        self.startpoint = startpoint

    # all starts with adding page ranges to scrape to tasks queue
    def task_queue(self):
        for task in self.tasks:
            self.queue.put(task)
        return

    def create_process(self):
        # make sure the queue is not empty before getting tasks from it
        pages = self.queue.get() if self.queue.qsize() > 0 else None
        # initializing scraper class first and unpacking args
        bs = BookScraper(self.startpoint, *pages)
        # start process with scraper's run() method
        process = mp.Process(target=bs.run)
        self.processes_list.append(process)
        process.start()
        return process

    def run(self):
        # initialize the queue
        self.task_queue()
        for p in range(self.num_of_processes):
            process = self.create_process()
            print(f"Process {p} started.")
        # start running the tasks
        for process in self.processes_list:
            process.join()
        # check if any process have failed and restart it
        while any(process.is_alive() for process in self.processes_list):
            self.is_alive()
        self.stop()
        return

    def is_alive(self):
        new_processes = []
        # iterate over copy of the process list, to keep integrity when removing processes
        for process in self.processes_list.copy():
            if not process.is_alive():
                self.processes_list.remove(process)
                new_process = self.create_process()
                new_processes.append(new_process)
        for p in new_processes:
            p.join()
        return

    def stop(self):
        for p in self.processes_list:
            p.terminate()
        # clear the process queue
        for p in range(self.num_of_processes):
            self.queue.put(None)
        return


def main():
    # I separated pages into three ranges, so each process has its own job
    pages = [(1, 17), (18, 34), (35, 50)]
    # according to docs, 'spawn' method is recommended on Windows
    # mp.set_start_method("spawn")
    pm = ProcessManager('https://books.toscrape.com/', pages, len(pages))
    pm.run()
    return True


if __name__ == "__main__":
    main()
