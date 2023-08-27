import requests
from bs4 import BeautifulSoup
from datetime import datetime
from database import Database
import time
import schedule
import gdown
from bot import Bot
import os

class Crawler:
    KEYWORDS = ["uefs", "universidade estadual de feira de santana", "universidade", "greve", "transporte", "ônibus", "paraliza ", "paralizam"]
    
    def request_page(self, url: str):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except Exception as e:
            print(e)
            return None

    def execute(self):
        self.extract_from_acordacidade(max_range=2)
        self.extract_from_uefs()

    def insert_db(self, data:dict):
        db = Database()
        db.insert(data)
  
    def check_exists(self, uri:str):
        db = Database()
        return db.exists(uri)
    
    def post_twitter(self, news:dict):
        try:
            image_path = ""

            if(news['img'] != ""):
                if not os.path.exists('tmp'):
                    os.makedirs('tmp')
                
                image_path = f"/tmp/{news['external_id']}.jpg"
                
                gdown.download(news['img'], image_path, quiet=False)
            
            bot = Bot()
            bot.post(news['title'], news['description'], news['uri'], image_path)
        except Exception as e:
            print("Could not post twitter: {}".format(str(e)))
            raise e

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
     
                    if(self.check_exists(uri)):
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
                        'img': img or "",
                        'description': description,
                        'date': final_date
                    }

                    self.insert_db(data)
                    
                    data['img'] = ""
                    len_twitter_post = len(data['title']) + len(data['description']) + len(data['uri'])
                    if((len_twitter_post) > 280):
                        data['description'] = data['description'][:(len_twitter_post - len(data['description']) - 277)] + "..."
                    self.post_twitter(data)
    
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
            
            p = news.find('p')
            if(p is not None):
                img = p.find('img')
                if(img is not None):
                  data['img'] = img.attrs['src']
                description = ((p.text.strip()).replace('\t', '')).replace('Leia mais', '')
                data['description'] = description.replace('››', '')
                

            self.insert_db(data)
            data['img'] = ""
            
            len_twitter_post = len(data['title']) + len(data['description']) + len(data['uri'])
            if((len_twitter_post) > 280):
                data['description'] = data['description'][:(len_twitter_post - len(data['description']) - 277)] + "..."
            self.post_twitter(data)

if __name__ == "__main__":
    crawler = Crawler()

    def job():
        print("\n Execute job. Time: {}".format(str(datetime.now())))
        crawler.execute()
    
    schedule.every(2).minutes.do(job)
    
    while True:
        schedule.run_pending()
        time.sleep(1)