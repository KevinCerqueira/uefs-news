import time
import os
import gdown
from pyshorteners import Shortener
from uefs_br import UefsBr
from acorda_cidade import AcordaCidade
from g1 import G1
from bot import Bot
from core import Core
from database import Database


class Main(Core):
    POST_WITH_IMAGE: bool = False
    CHARACTER_LIMIT: int = 280
    EXTRA_LIMIT: int = 10
    uefs: UefsBr
    ac: AcordaCidade
    g1: G1
    bot: Bot
    db: Database
    premium: bool

    def __init__(self) -> None:
        super().__init__(origin=self.__class__.__name__)
        self.uefs = UefsBr()
        self.ac = AcordaCidade(max_range=5)
        self.g1 = G1()
        self.bot = Bot()
        self.db = Database()
        self.premium = False

    def schedule(self, minutes: int = 2, duration: int = 0) -> None:
        if duration == 0:
            self.log.info("Running forever...")
            while True:
                self.execute()
                time.sleep(minutes * 60)
        else:
            self.log.info("Running for {}".format(duration))
            max_iterations = duration // minutes
            counter = 0
            while counter < max_iterations:
                self.execute()
                time.sleep(minutes * 60)
                counter += 1

            self.log.info("The schedule ended after {} iterations..".format(counter))

    def execute(self) -> None:
        all_news = list()
        self.log.debug("Executing job...")

        news_uefs = self.uefs.execute()
        if news_uefs is not None:
            all_news.append(news_uefs)

        news_ac = self.ac.execute()
        if news_ac is not None:
            all_news.append(news_ac)

        news_g1 = self.g1.execute()
        if news_g1 is not None:
            all_news.append(news_g1)

        for news in all_news:
            try:
                result = self.db.get_one(news["uri"], news["external_id"])
                if result is not None:
                    if "posted" in result:
                        if result["posted"]:
                            continue
                        elif self.post(result):
                            self.db.update_one(result["_id"], {"posted": True})
                            self.log.info("News ID {} posted and updated...".format(str(result["_id"])))
                else:
                    post = self.post(dict(news.copy()))
                    if post:
                        news['posted'] = True
                        self.db.insert(news)
                        self.log.info("New News posted and created...")

            except Exception as e:
                self.log.error(str(e))
                raise e

    def post(self, news: dict) -> bool:
        try:
            image_path = ""
            if news["img"] != "" and self.POST_WITH_IMAGE:
                if not os.path.exists("tmp"):
                    os.makedirs("tmp")
                image_path = f"/tmp/{news['external_id']}.jpg"
                gdown.download(news["img"], image_path, quiet=False)

            theme = self.get_theme(news["title"], news["source"])
            news["title"] = "{} {}".format(theme, news["title"])
            news["uri"] = self.short_url(news["uri"])

            if news["source"] != "AcordaCidade":
                news["uri"] = "🔗 " + news["uri"]

            news["description"] = "📌 " + str(news["description"].replace("\n", ""))

            len_twitter_post = len(news["title"]) + len(news["description"]) + len(news["uri"]) + self.EXTRA_LIMIT

            if (not self.premium) and len_twitter_post > self.CHARACTER_LIMIT:
                extra_chars = len(news["title"]) + len(news["uri"]) + self.EXTRA_LIMIT
                available_space = self.CHARACTER_LIMIT - extra_chars
                news["description"] = news["description"][:available_space] + "..."

            self.log.debug("News: {}".format(str(news)))
            self.log.debug("Len total post: {}".format(len_twitter_post))
            self.log.debug("Len description: {}".format(len(news["description"])))
            self.log.debug("Len cut: {}".format(int(self.CHARACTER_LIMIT - len(news["title"]) - len(news["uri"]) - 5)))
            self.log.debug("Len final: {}".format(len(news["title"] + news["description"] + news["uri"])))

            return self.bot.post(news["title"], news["description"], news["uri"], image_path)
        except Exception as e:
            self.log.error(
                "Could not post twitter - POST {}:{} - ERROR {}".format(news["title"], news["description"], str(e))
            )
            return False

    @staticmethod
    def short_url(url: str) -> str:
        s = Shortener()
        new_url = s.tinyurl.short(url)
        return new_url

    def get_theme(self, title: str, origin: str = "UefsBr") -> str:
        theme = ""
        themes = {
            "greve": "🚨 GREVE:",
            "paraliza": "🚨 PARALIZAÇÃO:",
            "paralizam": "🚨 PARALIZAÇÃO:",
            "uefs": "🏫 CAMPUS:",
            "universidade": "🏫 CAMPUS:",
            "universidades": "🏫 CAMPUS:",
            "transporte": "🚍 TRANSPORTE:",
            "ônibus": "🚍 TRANSPORTE:",
            "UefsBr": "🏫 CAMPUS:",
            "G1": "📣 G1:",
            "AcordaCidade": "📣 ACORDA CIDADE:"
        }

        if 'greve' in title:
            return themes['greve']
        elif 'paraliza' in title:
            return themes['paraliza']
        else:
            for keyword in os.getenv("KEYWORDS"):
                if keyword in title.lower():
                    theme = themes.get(keyword, "")
                    if theme != "":
                        break

        if theme == "":
            theme = themes[origin]

        self.log.info(f"Title: {title}. THEME: {theme}")
        return theme


if __name__ == "__main__":
    main = Main()
    main.schedule(minutes=3)
