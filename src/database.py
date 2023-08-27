from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

class Database:
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    COLUMNS = ['external_id', 'uri', 'title', 'img', 'description', 'date']	
 
    def __init__(self, fast:bool = False):
        load_dotenv()
        self.connect_database()
  
    def connect_database(self):
        client = MongoClient(os.getenv('DB_URI'))
        db = client[os.getenv('DB_DATABASE')]
        self.news = db.news
  
    def exists(self, uri:str) -> bool:
        try:
            query = {'uri': uri}
            return self.news.count_documents(query) > 0
        except Exception as e:
            print(e)
            raise e

    def insert(self, data:dict):
        if(self.exists(data['uri'])):
            return
        try:
            self.news.insert_one(data)
            return True
        except Exception as e:
            print(e)
            raise e

    def select(self, args:dict):
        query = dict()
        if('title' in args):
            query["title"] = {"$regex": f".*{args['title']}*.", "$options": "i"}
        if('description' in args):
            query["description"] = {"$regex": f".*{args['description']}*.", "$options": "i"}
            
        if('start_date' in args and 'end_date' in args):
            start_date = datetime.strptime(args['start_date'], self.DATE_FORMAT)
            end_date = datetime.strptime(args['end_date'], self.DATE_FORMAT)
            query['date'] = {'$gte': start_date, '$lte': end_date}
        elif('start_date' in args):
            start_date = datetime.strptime(args['start_date'], self.DATE_FORMAT)
            query['date'] = {'$gte': start_date}
        elif('end_date' in args):
            end_date = datetime.strptime(args['end_date'], self.DATE_FORMAT)
            query['date'] = {'$lte': end_date}
        
        order = 'date'
        sort = -1
        
        if('order_column' in args):
            order = args['order_column']
        if('order_type' in args and args['order_type'] == 'asc'):
            sort = 1
    
        result = self.news.find(query).sort(order, sort)
        if('limit' in args):
            result = result.limit(int(args['limit']))
        if('offset' in args):
            result = result.skip(int(args['offset']))

        response = []
        for news in result:
            response.append({'external_id': news['external_id'], 'title': news['title'], 'uri': news['uri'], 'img': news['img'], 'description': news['description'], 'date': datetime.strftime(news['date'], self.DATE_FORMAT)})
        return response
 
if __name__ == "__main__":
    db = Database()
    