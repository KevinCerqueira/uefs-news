import requests
from bs4 import BeautifulSoup
from datetime import datetime
from database import Database
import time
import schedule
import gdown
from bot import Bot
import os
from pyshorteners import Shortener
import re

class Crawler:
    TWITTER_PREMIUM = False
    KEYWORDS = ["uefs", "universidade estadual de feira de santana", "universidade", "greve", "transporte", "ônibus", "paraliza ", "paralizam"]
    
    def request_page(self, url: str, deep_request:bool = False):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            if(deep_request and 'window.location.replace' in response.text):
                soup = BeautifulSoup(response.text, 'html.parser')
                script = soup.find('script', string=re.compile('window.location.replace'))
                new_url = re.search(r'window.location.replace\("(.*?)"\)', script.string).group(1)
                response = requests.get(new_url)
                soup =  BeautifulSoup(response.text, 'html.parser')
            return soup
        except Exception as e:
            print(e)
            return None

    def execute(self):
        self.extract_from_acordacidade(max_range=2)
        self.extract_from_uefs()
        self.extract_from_g1()

    def insert_db(self, data:dict):
        db = Database()
        db.insert(data)
  
    def check_exists(self, uri:str, external_id:str = ""):
        db = Database()
        return db.exists(uri, external_id)
    
    def post_twitter(self, news:dict):
        try:
            image_path = ""

            if(news['img'] != ""):
                if not os.path.exists('tmp'):
                    os.makedirs('tmp')
                
                image_path = f"/tmp/{news['external_id']}.jpg"
                
                gdown.download(news['img'], image_path, quiet=False)
            
            if("www.uefs.br" in news['uri']):
                theme = self.get_theme(news['title'], "uefs")
            elif "www.acordacidade.com.br" in news['uri']:
                theme = self.get_theme(news['title'], "ac")
            elif "g1.globo.com" in news['uri']:
                theme = self.get_theme(news['title'], "g1")
            else:
                theme = self.get_theme(news['title'])
            
            title_original = news['title']
            news['title'] = f"{theme} {news['title']}"
            uri_original = str(news['uri'].replace("Link: ", ""))
            news['uri'] = self.short_url(uri_original)
            
            len_twitter_post = len(news['title']) + len(news['description']) + len(news['uri'])
            
            if(news['img'] != ""):
                len_twitter_post += 7
                
            if((not self.TWITTER_PREMIUM) and (len_twitter_post) > 280):
                news['description'] = news['description'][:280 - len(news['title']) - len(news['uri']) - 5] + "..."

            bot = Bot()
            print(news, len_twitter_post)
            print(len(news['title']) + len(news['description']) + len(news['uri']), 280 - len(news['title']) - len(news['uri']) - 3)
            print(len(news['description']))
            print(len(news['title']+ news['description']+ news['uri']))
            bot.post(news['title'], news['description'], news['uri'], image_path)
            news['uri'] = uri_original
            news['title'] = title_original
            return True
        except Exception as e:
            print("Could not post twitter - POST {}:{} - ERROR {}".format(news['title'], news['description'], str(e)))
            return False
    
    def short_url(self, url:str):
        s = Shortener()
        new_url = s.tinyurl.short(url)
        return new_url
    
    def get_theme(self, title: str, origin: str = "") -> str:
        themes = {
            'greve': '🚨 GREVE:',
            'paraliza': '🚨 PARALIZAÇÃO:',
            'paralizam': '🚨 PARALIZAÇÃO:',
            'uefs': '🏫CAMPUS:',
            'universidade': '🏫 CAMPUS:',
            'transporte': '🚍 TRANSPORTE:',
            'ônibus': '🚍 TRANSPORTE:',
            'g1': '📣 G1:',
            'ac': '📣 ACORDA CIDADE:'
        }
        if(origin != ""):
            return themes[origin]
        
        for keyword in self.KEYWORDS:
            if keyword in title.lower():
                return themes.get(keyword, '')
        return ''
    
    def extract_from_acordacidade(self, max_range:int = 3):
        base_url = 'https://www.acordacidade.com.br/noticias/page/'
        
        for page in range(1, max_range):
            soup = self.request_page(base_url + str(page))
            
            if(soup == None):
                print("Could not extract news from acordacidade")
                return

            all_news = soup.find_all('a', {'class': 'noticia-3 card-archive'})
            for news in all_news:
                title = news.attrs['title']
                title = title.replace('››', '')
                
                if(any(word in title.lower() for word in self.KEYWORDS)):
                    external_id = news.attrs['id']
                    uri = news.attrs['href']
     
                    if(self.check_exists(uri, external_id)):
                        return

                    img = news.find('img')
                    if(img is not None):
                        img = img.attrs['src']
                    
                    content = news.find('div', {'class': 'conteudo'})
                    description = content.find('p', {'class': 'sub-text resumo-18'}).text
                    description = description.replace('››', '')
                    
                    date, hour = content.find('p', {'class': 'data-single'}).text.split(" às ")
                    final_date = datetime.strptime(date.strip() + " " + hour.strip().replace('h', ':'), "%d/%m/%Y %H:%M")
                    
                    data = {
                        'external_id': external_id,
                        'uri': uri,
                        'title': title,
                        'img': "",
                        'description': description,
                        'date': final_date
                    }


                    if(self.TWITTER_PREMIUM and ("..." in data['description'] or "" in data['description'] or "Leia mais" in data['description'])):
                        news_page = self.request_page(data['uri'])
                        data['description'] = news_page.find('p', {'class': 'sub-title'}).text
                    
                    if(self.post_twitter(data)):
                        data['img'] = img or ""
                        self.insert_db(data)
                    
    
    def extract_from_uefs(self):
        base_url = "https://uefs.br/"
        soup = self.request_page(base_url)
        
        if(soup == None):
            print("Could not extract news from uefs")
            return
        
        all_news = soup.find_all('li', {'class': ['even', 'odd']})
        for news in all_news:
            h2 = news.find('h2', {'class': 'title'})
            a = h2.find('a')
            title = (a.text.strip()).replace('\t', '')
            title = title.replace('››', '')
            uri = a.attrs['href']
            date = datetime.strptime(news.find('span', {'class': 'date'}).text, "%d/%m/%Y %H:%M")
            external_id = 'post-uefs-' + str(date.strftime("%Y%m%d%H%M"))
   
            if(self.check_exists(uri)):
                return
   
            data = {
                'external_id': external_id,
                'uri': uri,
                'title': title,
                'img': "",
                'description': "",
                'date': date
            }
            
            img = ""
            p = news.find('p')
            if(p is not None):
                img = p.find('img')
                if(img is not None):
                  img = img.attrs['src']
                description = ((p.text.strip()).replace('\t', '')).replace('Leia mais', '')
                data['description'] = description.replace('››', '')
                
            if(data['description'] == ""):
                news_page = self.request_page(data['uri'])
                data['description'] = news_page.find('div', {'id': 'story_text'}).text


            if(self.TWITTER_PREMIUM and ("..." in data['description'] or "" in data['description'] or "Leia mais" in data['description'])):
                news_page = self.request_page(data['uri'])
                data['description'] = news_page.find('div', {'id': 'story_text'}).text
                
            
            if(self.post_twitter(data)): 
                data['img'] = img or ""
                self.insert_db(data)
            
    
    def extract_from_g1(self):
        soup = self.request_page("https://g1.globo.com/busca/?q=uefs&page=1&order=recent&species=not%C3%ADcias&from=now-1h")
        if(soup == None):
            return
        all_news = soup.find_all('div', {'class': 'widget--info__text-container'})
        for news in all_news:
            a = news.find('a')
            uri = a.attrs['href'].replace("//g1.", "https://g1.")
            
            if(self.check_exists(uri)):
                return
            
            response = self.request_page(uri, deep_request=True)
            if(response == None):
                return
            title = a.find('div', {'class': 'widget--info__title product-color'})
            if(title == None):
                return
            title = title.text.strip()
            description = response.find('h2', {'class': 'content-head__subtitle', 'itemprop': 'alternativeHeadline'})
            if(description != None):
                description = description.text.strip()
            date = datetime.strptime(response.find('time', {'itemprop': 'datePublished'}).attrs['datetime'], "%Y-%m-%dT%H:%M:%S.%fZ")
            external_id = 'post-g1-' + str(date.strftime("%Y%m%d%H%M"))
            
            if(self.check_exists(uri, external_id)):
                return
            
            data = {
                'external_id': external_id,
                'uri': uri,
                'title': title,
                'img': "",
                'description': description,
                'date': date
            }
            
            # img = response.find('amp-img').attrs['src']
            # if(img is not None):
            #     data['img'] = img
            
            # if()
            
            if(self.post_twitter(data)):
                self.insert_db(data)
    
    
if __name__ == "__main__":
    crawler = Crawler()
    crawler.execute()
    
    def job():
        print("\n Execute job. Time: {}".format(str(datetime.now())))
        crawler.execute()
    
    schedule.every(2).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)