from bs4 import BeautifulSoup
import requests
import re
from core import Core


class Scrap(Core):
    url: str

    def __init__(self, url: str = ""):
        super().__init__(origin=self.__class__.__name__)
        self.url = url

    def request(self, url: str = "", deep_request: bool = False) -> BeautifulSoup | None:
        try:
            if url != "":
                self.url = url

            response = requests.get(self.url)
            soup = BeautifulSoup(response.text, "html.parser")
            if deep_request and "window.location.replace" in response.text:
                soup = BeautifulSoup(response.text, "html.parser")
                script = soup.find('script', string=re.compile("window.location.replace"))
                new_url = re.search(r'window.location.replace\("(.*?)"\)', script.string).group(1)
                response = requests.get(new_url)
                soup = BeautifulSoup(response.text, "html.parser")

            return soup
        except Exception as e:
            self.log.error(str(e))
            return None
