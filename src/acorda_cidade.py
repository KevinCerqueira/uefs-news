from datetime import datetime
from crawler import Crawler


class AcordaCidade(Crawler):

    def __init__(self, max_range: int = 4) -> None:
        super().__init__(
            base_url="https://www.acordacidade.com.br/ultimas-noticias/",
            max_range=max_range,
            origin=self.__class__.__name__
        )

    def execute(self, twitter_premium: bool = False) -> dict | None:
        self.log.debug("Executing request")
        first = True
        for page in range(1, self.max_range):

            url = self.base_url
            if not first:
                url = url + 'page/' + str(page)
                first = False

            soup = self.scrap.request(f"{url}")
            if soup is None:
                self.log.error("Could not extract news from acordacidade")
                return

            all_news = soup.find_all('article', {"class": "feed"})
            for news in all_news:
                article = news.find("a", {"class": "feed-link"})
                title = article.attrs["title"]
                title = title.replace("››", '').replace('&nbsp;', '')
                if any(word in title.lower() for word in self.keywords):
                    external_id = "post-ac-" + str(datetime.date(datetime.now()).strftime("%Y%m%d%H%M"))
                    uri = news.attrs["href"]

                    # img = news.find("img")
                    # if img is not None:
                    #     img = img.attrs["src"]

                    content = article.find("div", {"class": "feed-body"})
                    description = content.find('p', {"class": "feed-excert"}).text
                    description = description.replace("››", '')

                    # date, hour = content.find('p', {"class": "data-single"}).text.split(" às ")
                    # final_date = datetime.strptime(
                    #     date.strip() + ' ' + hour.strip().replace('h', ':'),
                    #     "%d/%m/%Y %H:%M"
                    # )

                    data = {
                        "external_id": external_id,
                        "uri": uri,
                        "title": title,
                        "img": '',
                        "description": description,
                        "date": datetime.now(),
                        "source": self.__class__.__name__,
                        "posted": False
                    }
                    if twitter_premium and (
                            "..." in data["description"]
                            or "" in data["description"]
                            or "Leia mais" in data["description"]
                    ):
                        news_page = self.scrap.request(data["uri"])
                        data["description"] = news_page.find('p', {"class": "sub-title"}).text

                    return data
