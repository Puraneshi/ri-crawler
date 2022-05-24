from typing import Optional

from bs4 import BeautifulSoup
from threading import Thread
import requests
from urllib.parse import urlparse, ParseResult


class PageFetcher(Thread):
    def __init__(self, obj_scheduler):
        super().__init__()
        self.obj_scheduler = obj_scheduler

    def request_url(self, obj_url: ParseResult) -> Optional[bytes] or None:
        """
        :param obj_url: Instância da classe ParseResult com a URL a ser requisitada.
        :return: Conteúdo em binário da URL passada como parâmetro, ou None se o conteúdo não for HTML
        """

        headers = {'User-Agent':
                   self.obj_scheduler.usr_agent}

        response = requests.get(obj_url.geturl(), headers=headers)
        if 'html' in response.headers['Content-Type']:
            return response.content
        else:
            return None

    def discover_links(self, obj_url: ParseResult, depth: int, bin_str_content: bytes):
        """
        Retorna os links do conteúdo bin_str_content da página já requisitada obj_url
        """
        soup = BeautifulSoup(bin_str_content, features="lxml")

        for link in soup.select('a[href]'):
            obj_new_url = urlparse(link['href'])
            if not obj_new_url.netloc:
                obj_new_url = obj_new_url._replace(scheme=obj_url.scheme)
                obj_new_url = obj_new_url._replace(netloc=obj_url.netloc)
            is_same_domain = obj_new_url.netloc == obj_url.netloc
            if is_same_domain:
                new_depth = depth+1
            else:
                new_depth = 0

            yield obj_new_url, new_depth

    def crawl_new_url(self):
        """
        Coleta uma nova URL, obtendo-a do escalonador
        """
        # Solicita ao escalonador uma nova URL
        bool_can_fetch = False
        obj_url, depth = None, None
        while not bool_can_fetch:
            pack = self.obj_scheduler.get_next_url()
            if pack:
                obj_url, depth = pack

            bool_can_fetch = self.obj_scheduler.can_fetch_page(obj_url)

        # Faz requisição e obtem o resultado em binário
        try:
            bin_url_content = self.request_url(obj_url)
        except:
            bin_url_content = None

        # Caso a URL seja um HTML válido, imprime esta URL e extrai seus links
        if bin_url_content:
            self.obj_scheduler.count_fetched_page()
            # print(obj_url.geturl())

            for i_obj_url, i_depth in self.discover_links(obj_url, depth, bin_url_content):
                self.obj_scheduler.add_new_page(i_obj_url, i_depth)

        pass

    def run(self):
        """
        Executa coleta enquanto houver páginas a serem coletadas
        """

        # check if obj_url dict is empty
        while not self.obj_scheduler.has_finished_crawl():
            self.crawl_new_url()

        pass
