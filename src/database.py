from pymongo.mongo_client import MongoClient
from datetime import datetime
import os
from core import Core
import re
from bson.objectid import ObjectId


class Database(Core):
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    COLUMNS = ["external_id", "uri", "title", "img", "description", "date", "posted"]
 
    def __init__(self):
        super().__init__(origin=self.__class__.__name__)
        self.news = self.connect()

    @staticmethod
    def connect() -> MongoClient:
        client = MongoClient(os.getenv('DB_URI'))
        database = client[os.getenv('DB_DATABASE')]
        return database.news
  
    def exists(self, uri: str, external_id: str = '') -> bool:
        try:
            query = {"uri": uri}
            if external_id != '':
                query = {"$or": [{"uri": uri}, {"external_id": external_id}]}
            return self.news.count_documents(query) > 0
        except Exception as e:
            self.log.error(str(e))
            raise e

    def insert(self, data: dict) -> bool | None:
        if self.exists(data["uri"], data["external_id"]):
            return
        try:
            self.news.insert_one(data)
            return True
        except Exception as e:
            print(e)
            raise e

    def update(self, uri: str, external_id: str, values: dict) -> bool:
        try:
            query = {"uri": uri}
            if external_id != '':
                query = {"$or": [{"uri": uri}, {"external_id": external_id}]}
            return self.news.update_one(query, {'$set': values})
        except Exception as e:
            self.log.error(str(e))
            raise e

    def update_one(self, news_id: ObjectId, values: dict) -> bool:
        try:
            return self.news.update_one({"_id": news_id}, {'$set': values})
        except Exception as e:
            self.log.error(str(e))
            raise e

    def get_one(self, uri: str, external_id: str) -> dict | None:
        try:
            query = {"$or": [{"uri": uri}, {"external_id": external_id}]}
            return self.news.find_one(query)
        except Exception as e:
            self.log.error(str(e))
            raise e

    def select(self, args: dict):
        query = dict()
        if "title" in args:
            query["title"] = {"$regex": ".*{}*.".format(args["title"]), "$options": "i"}
        if "description" in args:
            query["description"] = {"$regex": ".*{}*.".format(args["description"]), "$options": "i"}
            
        if "start_date" in args and "end_date" in args:
            start_date = datetime.strptime(args["start_date"], self.DATE_FORMAT)
            end_date = datetime.strptime(args["end_date"], self.DATE_FORMAT)
            query["date"] = {"$gte": start_date, "$lte": end_date}
        elif "start_date" in args:
            start_date = datetime.strptime(args["start_date"], self.DATE_FORMAT)
            query["date"] = {"$gte": start_date}
        elif "end_date" in args:
            end_date = datetime.strptime(args["end_date"], self.DATE_FORMAT)
            query["date"] = {"$lte": end_date}
        
        order = "date"
        sort = -1
        
        if "order_column" in args:
            order = args["order_column"]
        if "order_type" in args and args["order_type"] == "asc":
            sort = 1
    
        result = self.news.find(query).sort(order, sort)
        if "limit" in args:
            result = result.limit(int(args["limit"]))
        if "offset" in args:
            result = result.skip(int(args["offset"]))

        response = []
        for news in result:
            response.append({
                "external_id": news["external_id"],
                "title": news["title"],
                "uri": news["uri"],
                "img": news["img"],
                "description": news["description"],
                "date": datetime.strftime(news["date"], self.DATE_FORMAT)
            })

        return response


if __name__ == "__main__":
    db = Database()
    