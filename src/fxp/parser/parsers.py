import os
import json
import pickle
import requests
from bs4 import BeautifulSoup as BS
from abc import ABC, abstractmethod

from fxp.parser import DEFAULT_USER_AGENT, HOST, PREVIEW_URL, BASE_DIR


class _Base(type):
    def __init__(cls, name, bases, attr_dict): 
        super().__init__(name, bases, attr_dict)
    def __call__(cls, *args, **kwargs):
        obj = super().__call__(*args,**kwargs)
        if cls.__name__ == "Preview":
            cls.__bases__[0].page=obj._Preview__num_page
        return obj


class BaseMeta(metaclass=_Base):
    """Bate Meta Class"""


class BaseParser(BaseMeta):
    __metaclass__ = ABC

    def __init__(self, user_agent: str = None):
        self._user_agent = user_agent if user_agent is not None else DEFAULT_USER_AGENT

    def _get_page(self, url):
        if hasattr(self, "page"):
            if self.page < 1 :
                raise ValueError("Page is < 1")
        response = requests.get(
            url,
            headers={
                "User-Agent": self._user_agent,
            },
        )
        if hasattr(self, "page"):
            if not response.url.endswith(str(self.page)):
                if self.page != 1:
                    raise ValueError("Page is very big!")
        if response.status_code == 200:
            return BS(response.text, features="html5lib")
        raise ValueError("Response not 200")

    @abstractmethod
    def save_to_file(self, name: str) -> None:
        """Save news to file
        :param name: file name
        :type name: str
        """

    @abstractmethod
    def save_to_json(self, name: str) -> None:
        """Save news to json file
        :param name: file name
        :type name: str
        """


class Preview(BaseParser):
    def __init__(self, **kwargs):
        super().__init__(kwargs.get("user_agent"))
        self.__num_page = kwargs.get("page") if kwargs.get("page") is not None else 1
        self.__links = []

    def get_links(self):
        try:
            html = self._get_page(PREVIEW_URL.format(HOST, self.__num_page))
        except ValueError as error:
            print(error)
            # self.__links = []
        else:
            box = html.find("div", attrs={"class": "largeTitle"})
            if box is not None:
                articles = box.find_all(
                    "article", attrs={"class": "js-article-item articleItem"}
                )
                for article in articles:
                    link = article.find("a", attrs={"class": "title"})
                    self.__links.append(HOST + link.get("href"))
            else:
                self.__links = []


    def __iter__(self):
        self.__cursor = 0
        return self
       
    def __next__(self):
        if self.__cursor == len(self.__links):
            raise StopIteration
        try:
            return self.__links[self.__cursor]
        finally:
            self.__cursor += 1

    def __getitem__(self, index):
        try:
            return self.__links[index]
        # except ValueError as error:
        #     print(error)

    def save_to_file(self, name):
        path = os.path.join(BASE_DIR, name + ".bin")
        pickle.dump(self.__links, open(path, "wb"))

    def save_to_json(self, name):
        path = os.path.join(BASE_DIR, name + ".json")
        json.dump(self.__links, open(path, "w"))


class NewsParser(BaseParser):
    def __init__(self, url):
        self._url = url
        self.news = {}

    def get_news(self):
        try:
            html = self._get_page(self._url)
        except ValueError as error:
            print(error)
        else:
            box = html.find("section", attrs={"id": "leftColumn"})
            if box is not None:
                self.news["head"] = box.find("h1", atrrs={"class": "arcicleHeader"}).text
                box_data = box.find("div", attrs={"class":"contentSectionDetails"})
                news_date = box_data.find("span").text

if __name__ == "__main__":
    parser = Preview(page=2)
    parser.get_links()
    # print(parser._Preview__links)
    # parser.save_to_json("tmp_links_5")
    # parser.save_to_file("tmp_links_5")
    # for link in parser:
    #     print(link)
    a = parser[0:3]
    print(a)