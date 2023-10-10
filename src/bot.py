import tweepy
from dotenv import load_dotenv
import os

class Bot:
    def __init__(self):
        load_dotenv()
        consumer_key = os.getenv('TWITTER_CONSUMER_KEY')
        consumer_secret = os.getenv('TWITTER_CONSUMER_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        
        self.client = tweepy.Client(
            bearer_token=r"{}".format(bearer_token),
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )
        
        auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret)
        auth.set_access_token(
            access_token,
            access_token_secret,
        )
        self.api = tweepy.API(auth)


    def post(self, title:str, description:str, link:str, image_path:str):
        if(image_path != ""):
            message = f"{title}\n\n{description}\n\n Link: {link}"
            media = self.api.media_upload(filename=image_path)
            media_id = media.media_id
            self.client.create_tweet(text=message, media_ids=[media_id])
        else:
            message = f"{title}\n\n{description}\n\n {link}"
            self.client.create_tweet(text=message)
            