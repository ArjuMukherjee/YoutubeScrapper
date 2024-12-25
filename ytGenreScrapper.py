import csv
import time
from selenium.webdriver.common.keys import Keys
from ytscrapper import VideoScrapper
from selenium.webdriver.common.by import By

class GenreVideoScrapper(VideoScrapper):
    def __init__(self, genre):
        self.genre = genre
        self.base_url = "https://www.youtube.com/results?search_query="
        self.video_urls = []
        super().__init__(None)

    def search_videos(self,n):
        search_url = f"{self.base_url}{self.genre}"
        self.setup_driver()
        self.driver.get(search_url)
        time.sleep(3)  # Allow time for the page to load

        while len(self.video_urls) < n:
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

    def scrape_video_details(self):
        video_details = []
        for i, url in enumerate(self.video_urls):
            print(f"Scraping video {i + 1}/{len(self.video_urls)}: {url}")
            self.url = url
            details = self.get_page_detail()
            video_details.append(details)
        return video_details

    def save_to_csv(self, video_details, output_file="video_details.csv"):
        if video_details:
            keys = video_details[0].keys()
            with open(output_file, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=keys)
                writer.writeheader()
                writer.writerows(video_details)
            print(f"Data saved to {output_file}")

if __name__ == "__main__":
    print("Enter the genre to search:")
    genre = input("> ")
    print("Enter the number of videos to scrape:")
    n = int(input("> "))
    scraper = GenreVideoScrapper(genre)
    scraper.search_videos(n)
    video_data = scraper.scrape_video_details()
    scraper.save_to_csv(video_data)
