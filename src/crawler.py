from scrap import Scrap
from database import Database
import os
from core import Core


class Crawler(Core):
    base_url: str
    db: Database
    max_range: int
    scrap: Scrap
    keywords: list

    def __init__(self, base_url: str, max_range: int = 2, origin: str = "Crawler") -> None:
        super().__init__(origin)
        self.max_range = max_range
        self.base_url = base_url
        self.db = Database()
        self.scrap = Scrap(self.base_url)
        self.keywords = str(os.getenv("KEYWORDS")).split(',')

    def execute(self, twitter_premium: bool = False) -> dict | None:
        pass


if __name__ == "__main__":
    c = Crawler("uefs.br")
