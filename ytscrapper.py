from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import requests
import time
import json
import os
import re

class VideoScrapper:
    def __init__(self, url):
        self.url = url
        self.driver = None

    def clean_text(self, str):
        new_str = ''
        for c in str:
            if c == '\n' or c == '(' or c == ')' or c == '|' or not (c.isalpha() or c == ' '):
                continue
            new_str += c
        return new_str.strip()

    def setup_driver(self):
        service = Service(os.path.join(os.getcwd(), 'chromedriver/chromedriver.exe'))
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(service=service, options=options)

    def scroll_to_load_comments(self):

        self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight/4);")
        time.sleep(2)  # Wait for new content to load
    
    def get_captions(self, page_source):

        try:

            match = re.search(r'ytInitialPlayerResponse\s*=\s*({.*?});', page_source)
            if match:
                player_response = json.loads(match.group(1))
                captions = player_response.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
                if not captions:
                    return "No captions available"

                caption_url = captions[0].get('baseUrl')
                if not caption_url:
                    return "Caption URL not found"

                response = requests.get(caption_url)
                soup = BeautifulSoup(response.content, 'xml')

                # Extract text from each <text> tag in the XML
                caption_texts = [text_tag.text for text_tag in soup.find_all('text')]
                return "\n".join(caption_texts)
            else:
                return "Player response not found"
        except Exception as e:
            return f"Error fetching captions: {e}"
        
    def get_recording_location(self, soup):

        try:
            location_element = soup.find('yt-formatted-string', {'class': 'style-scope ytd-video-secondary-info-renderer'})
            if location_element and 'location' in location_element.text.lower():
                return location_element.text.strip()
            return "Location not available"
        except Exception as e:
            return f"Error fetching location: {e}"
    
    def get_likes(self, soup):
        try:
            # Find the button with the aria-label containing likes information
            like_button = soup.find("button", {"aria-label": lambda x: x and "like this video" in x})
            if like_button:
                likes_text = like_button["aria-label"]
                # Extract the numeric part using regex
                likes_match = re.search(r"([\d,]+)", likes_text)
                if likes_match:
                    return likes_match.group(1).replace(",", "")  # Return likes as a plain number
            return "Likes not found"
        except Exception as e:
            return f"Error fetching likes: {e}"

    def get_page_detail(self):
        self.setup_driver()
        self.driver.get(self.url)
        time.sleep(5)
        
        # Scroll to load comments
        self.scroll_to_load_comments()

        # page_source
        page_source = self.driver.page_source
        caption = self.get_captions(page_source)

        soup = BeautifulSoup(page_source, 'lxml')

        video_detail = {}
        try:
            # Extract video details
            video_detail['url'] = soup.find('meta', attrs={'property':'og:url'}).get('content')
            video_detail['title'] = soup.find('meta',attrs={'name':'title'}).get('content')
            video_detail['description'] = soup.find('meta', itemprop='description').get('content')
            video_detail['channel-title'] = soup.find('body').find('div', id='columns').find('yt-formatted-string', id='text').a.text.strip()
            video_detail['likes'] = self.get_likes(soup)
            video_detail['views'] = soup.find('body').find('div', id='columns').find('div', id='bottom-row').find('div', id='info-container').find('yt-formatted-string', id='info').text.split('views')[0].strip()
            video_detail['published-at'] = soup.find('meta', itemprop="datePublished").get('content')
            video_detail['duration'] = soup.find('meta',itemprop='duration').get('content')[2:]
            video_detail['keywords'] = list(map(lambda x: x.strip(),soup.find('head').find('meta', attrs={'name': 'keywords'}).get('content').split(',')))
            video_detail["category"] = soup.select_one('meta[itemprop="genre"][content]').attrs['content']
            result = [c.text for c in soup.find('div', id='columns').find(
                'ytd-engagement-panel-section-list-renderer', attrs={'target-id': 'engagement-panel-structured-description'}).find_all('span', class_='yt-core-attributed-string--link-inherit-color', attrs={'dir': "auto", 'style': "color: rgb(19, 19, 19);"})]
            video_detail['topic-details'] = list(map(self.clean_text, result[:len(result) // 2]))
            video_detail['comments-count'] = soup.find('ytd-comments', {'id': 'comments'}).find('ytd-item-section-renderer',id='sections').find('div',id='header').find('h2',id='count').text.split(' ')[0].strip().replace(',','')
            caption_title = soup.find('div',id='columns').find('div',id='player').find('button',class_='ytp-subtitles-button ytp-button').attrs['title']
            if 'unavailable' not in caption_title:
                video_detail['caption'] = True
                video_detail['caption-content'] = self.get_captions(page_source)
            else:
                video_detail['caption'] = False
                video_detail['caption-content'] = None
            video_detail['location'] = self.get_recording_location(soup)

        except Exception as e:
            print(f"Error extracting details: {e}")
        finally:
            self.driver.quit()
            return video_detail

if __name__ == "__main__":
    print("Give the URL of the page")
    url = input("> ")
    if url == '':
        url = 'https://www.youtube.com/watch?v=XVv6mJpFOb0'
    vs = VideoScrapper(url)
    detail = vs.get_page_detail()
    print(detail)
