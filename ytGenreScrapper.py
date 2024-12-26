import csv
import time
import threading
import socket
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from ytscrapper import VideoScrapper
from selenium.webdriver.common.by import By

class GenreVideoScrapper(VideoScrapper):
    def __init__(self, genre):
        self.genre = genre
        self.base_url = "https://www.youtube.com/results?search_query="
        self.video_urls = []
        super().__init__(None)

    def search_videos(self, n):
        search_url = f"{self.base_url}{self.genre}"
        self.setup_driver()
        self.driver.get(search_url)
        time.sleep(3)  # Allow time for the page to load

        while len(self.video_urls) < n:
            self.wait_for_internet()
            videos = self.driver.find_elements(By.XPATH, "//a[@id='video-title']")
            for video in videos:
                url = video.get_attribute('href')
                if url and url not in self.video_urls:
                    self.video_urls.append(url)
                if len(self.video_urls) >= n:
                    break

            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(2)  # Allow time for new content to load

        self.driver.quit()

    def scrape_video_details(self, output_file="video_details.csv"):
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = None
            for i, url in enumerate(self.video_urls):
                print(f"Scraping video {i + 1}/{len(self.video_urls)}: {url}")
                self.url = url
                self.wait_for_internet()

                try:
                    details = self.get_page_detail()
                except (TimeoutException, WebDriverException) as e:
                    print(f"Error accessing video {url}: {e}. Retrying...")
                    self.wait_for_internet()
                    continue

                if not writer:
                    # Initialize CSV writer with headers from the first detail
                    keys = details.keys()
                    writer = csv.DictWriter(file, fieldnames=keys)
                    writer.writeheader()

                writer.writerow(details)
                print(f"Video {i + 1} details saved to {output_file}")

    @staticmethod
    def wait_for_internet():
        while not GenreVideoScrapper.check_internet():
            print("No internet connection. Retrying in 5 seconds...")
            time.sleep(5)

    @staticmethod
    def check_internet():
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=5)
            return True
        except OSError:
            return False

if __name__ == "__main__":
    def scrape_task():
        print("Enter the genre to search:")
        genre = input("> ")
        print("Enter the number of videos to scrape:")
        n = int(input("> "))
        scraper = GenreVideoScrapper(genre)
        scraper.search_videos(n)
        scraper.scrape_video_details()

    # Run the scraper in a separate thread
    scrape_thread = threading.Thread(target=scrape_task)
    scrape_thread.start()

    # Main thread can monitor other tasks or remain idle
    scrape_thread.join()
