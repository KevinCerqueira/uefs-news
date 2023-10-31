from datetime import datetime
from crawler import Crawler


class G1(Crawler):
    def __init__(self) -> None:
        super().__init__(
            base_url="https://g1.globo.com/busca/?q=uefs&page=1&order=recent&species=not%C3%ADcias",
            origin=self.__class__.__name__
        )

    def execute(self, twitter_premium: bool = False) -> dict | None:
        self.log.debug("Executing request")
        soup = self.scrap.request()
        if soup is None:
            self.log.error("empty soup")
            return

        all_news = soup.find_all("div", {"class": "widget--info__text-container"})
        for news in all_news:
            a = news.find('a')
            uri = a.attrs["href"].replace("//g1.", "https://g1.")

            response = self.scrap.request(url=uri, deep_request=True)
            if response is None:
                self.log.error("Empty deep_request response")
                return

            title = a.find("div", {"class": "widget--info__title product-color"})
            if title is None:
                self.log.error("Title not found")
                return

            title = title.text.strip()

            description = response.find("h2", {"class": "content-head__subtitle", "itemprop": "alternativeHeadline"})
            if description is None:
                self.log.error("Description not found")
                return

            description = description.text.strip()

            date = datetime.strptime(
                response.find("time", {"itemprop": "datePublished"}).attrs["datetime"],
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )
            external_id = "post-g1-" + str(date.strftime("%Y%m%d%H%M"))

            data = {
                "external_id": external_id,
                "uri": uri,
                "title": title,
                "img": "",
                "description": description,
                "date": date,
                "source": self.__class__.__name__,
                "posted": False
            }

            return data
