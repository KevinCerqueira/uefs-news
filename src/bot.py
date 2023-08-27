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

        auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret)
        auth.set_access_token(
            access_token,
            access_token_secret,
        )
        self.client_v1 = tweepy.API(auth)
        self.client_v2 = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

    def post(self, title:str, description:str, link:str, image_path:str):
        message = f"{title}\n\n{description}\n\n {link}"
        if(image_path != ""):
            media = self.client_v1.media_upload(filename=image_path)
            media_id = media.media_id
            self.client_v2.create_tweet(text=message, media_ids=[media_id])
        else:
            self.client_v2.create_tweet(text=message)
