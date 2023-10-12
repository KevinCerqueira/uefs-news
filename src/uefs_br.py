from datetime import datetime
from crawler import Crawler


class UefsBr(Crawler):
    def __init__(self) -> None:
        super().__init__(base_url="https://uefs.br/", origin=self.__class__.__name__)

    def execute(self, twitter_premium: bool = False) -> dict | None:
        self.log.debug("Executing request")
        soup = self.scrap.request()

        if soup is None:
            self.log.error("Could not extract news from uefs")
            return

        all_news = soup.find_all("li", {"class": ["even", "odd"]})
        for news in all_news:
            h2 = news.find("h2", {"class": "title"})
            a = h2.find('a')
            title = (a.text.strip()).replace('\t', '')
            title = title.replace("››", '')
            uri = a.attrs["href"]
            date = datetime.strptime(news.find("span", {"class": "date"}).text, "%d/%m/%Y %H:%M")
            external_id = "post-uefs-" + str(date.strftime("%Y%m%d%H%M"))

            data = {
                "external_id": external_id,
                "uri": uri,
                "title": title,
                "img": "",
                "description": "",
                "date": date,
                "posted": False
            }

            p = news.find('p')
            if p is not None:
                img = p.find("img")
                if img is not None:
                    data["img"] = img.attrs["src"]

                description = ((p.text.strip()).replace('\t', '')).replace("Leia mais", '')
                data["description"] = description.replace("››", '')

            if data["description"] == "":
                news_page = self.scrap.request(data["uri"])
                data["description"] = news_page.find("div", {"id": "story_text"}).text

            if twitter_premium and (
                    "..." in data["description"]
                    or "" in data["description"]
                    or "Leia mais" in data["description"]
            ):
                news_page = self.scrap.request(data["uri"])
                data["description"] = news_page.find("div", {"id": "story_text"}).text

            return data
