from datetime import datetime
from crawler import Crawler


class AcordaCidade(Crawler):

    def __init__(self, max_range: int = 2) -> None:
        super().__init__(
            base_url="https://www.acordacidade.com.br/noticias/page/",
            max_range=max_range,
            origin=self.__class__.__name__
        )

    def execute(self, twitter_premium: bool = False) -> dict | None:
        self.log.debug("Executing request")
        for page in range(1, self.max_range):
            soup = self.scrap.request(f"{self.base_url}{page}")

            if soup is None:
                self.log.error("Could not extract news from acordacidade")
                return

            all_news = soup.find_all('a', {"class": "noticia-3 card-archive"})
            for news in all_news:
                title = news.attrs["title"]
                title = title.replace("››", '')

                if any(word in title.lower() for word in self.keywords):
                    external_id = news.attrs["id"]
                    uri = news.attrs["href"]

                    img = news.find("img")
                    if img is not None:
                        img = img.attrs["src"]

                    content = news.find("div", {"class": "conteudo"})
                    description = content.find('p', {"class": "sub-text resumo-18"}).text
                    description = description.replace("››", '')

                    date, hour = content.find('p', {"class": "data-single"}).text.split(" às ")
                    final_date = datetime.strptime(
                        date.strip() + ' ' + hour.strip().replace('h', ':'),
                        "%d/%m/%Y %H:%M"
                    )

                    data = {
                        "external_id": external_id,
                        "uri": uri,
                        "title": title,
                        "img": '',
                        "description": description,
                        "date": final_date,
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
