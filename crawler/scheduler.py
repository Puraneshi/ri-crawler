from urllib import robotparser
from urllib.parse import ParseResult

from util.threads import synchronized
from time import sleep
from collections import OrderedDict
from .domain import Domain


class Scheduler:
    # tempo (em segundos) entre as requisições
    TIME_LIMIT_BETWEEN_REQUESTS = 20

    def __init__(self, usr_agent: str, page_limit: int, depth_limit: int, arr_urls_seeds):
        """
        :param usr_agent: Nome do `User agent`. Usualmente, é o nome do navegador, em nosso caso,  será o nome do
        coletor (usualmente, terminado em `bot`)
        :param page_limit: Número de páginas a serem coletadas
        :param depth_limit: Profundidade máxima a ser coletada
        :param arr_urls_seeds: Lista de URLs que serão as raízes da coleta

        Demais atributos:
        - `page_count`: Quantidade de página já coletada
        - `dic_url_per_domain`: Fila de URLs por domínio (explicado anteriormente)
        - `set_discovered_urls`: Conjunto de URLs descobertas, ou seja, que foi extraída em algum HTML e já adicionadas
        na fila - mesmo se já ela foi retirada da fila. A URL armazenada deve ser uma string.
        - `dic_robots_per_domain`: Dicionário armazenando, para cada domínio, o objeto representando as regras obtidas
        no `robots.txt`
        """
        self.usr_agent = usr_agent
        self.page_limit = page_limit
        self.depth_limit = depth_limit
        self.page_count = 0

        self.dic_url_per_domain = OrderedDict()
        self.set_discovered_urls = set()
        self.dic_robots_per_domain = {}

        for obj_url in arr_urls_seeds:
            if self.add_new_page(obj_url, 1):
                print(f"URL {obj_url.geturl()} inserida!")
            else:
                print(f"ERRO - URL {obj_url.geturl()} REPETIDA")

    @synchronized
    def count_fetched_page(self) -> None:
        """
        Contabiliza o número de paginas já coletadas
        """
        self.page_count += 1
        if not self.page_count % 100:
            print(f'The page count has reached a new milestone: {self.page_count}')

    def has_finished_crawl(self) -> bool:
        """
        :return: True se finalizou a coleta. False caso contrário.
        """
        if self.page_count >= self.page_limit or not self.dic_url_per_domain:
            return True
        return False

    @synchronized
    def can_add_page(self, obj_url: ParseResult, depth: int) -> bool:
        """
        :return: True caso a profundidade for menor que a maxima e a url não foi descoberta ainda. False caso contrário.
        """
        if depth <= self.depth_limit and obj_url.geturl() not in self.set_discovered_urls:
            return True
        return False

    @synchronized
    def add_new_page(self, obj_url: ParseResult, depth: int) -> bool:
        """
        Adiciona uma nova página
        :param obj_url: Objeto da classe ParseResult com a URL a ser adicionada
        :param depth: Profundidade na qual foi coletada essa URL
        :return: True caso a página foi adicionada. False caso contrário
        """
        # https://docs.python.org/3/library/urllib.parse.html
        if self.can_add_page(obj_url, depth):
            self.set_discovered_urls.add(obj_url.geturl())
            self.dic_url_per_domain.setdefault(
                Domain(
                    obj_url.netloc,
                    self.TIME_LIMIT_BETWEEN_REQUESTS),
                []).append((obj_url, depth+1))

            return True
        return False

    @synchronized
    def get_next_url(self) -> tuple:
        """
        Obtém uma nova URL por meio da fila. Essa URL é removida da fila.
        Logo após, caso o servidor não tenha mais URLs, o mesmo também é removido.
        """

        while self.dic_url_per_domain:
            for obj_domain in self.dic_url_per_domain:
                if obj_domain.is_accessible():
                    obj_domain.accessed_now()
                    obj_url, depth = self.dic_url_per_domain[obj_domain].pop(0)
                    if len(self.dic_url_per_domain[obj_domain]) == 0:
                        self.dic_url_per_domain.pop(obj_domain)
                    # print(f"Servidor {obj_domain} acessível! Resgatando próxima URL da fila...")
                    # print(f"URL {obj_url.geturl()} resgatada")
                    return obj_url, depth
            sleep(1)

    def can_fetch_page(self, obj_url: ParseResult) -> bool:
        """
        Verifica, por meio do robots.txt se uma determinada URL pode ser coletada
        Se ja registramos o robots.txt do dominio, acessamos no dicionario de robos
        se não registramos, criamos o parser do robots e cadastramos no dicionario
        """
        if obj_url.netloc not in self.dic_robots_per_domain:
            obj_robot_parser = robotparser.RobotFileParser()
            obj_robot_parser.set_url(f"{obj_url.scheme}://{obj_url.netloc}/robots.txt")
            try:
                obj_robot_parser.read()
                self.dic_robots_per_domain.setdefault(obj_url.netloc, obj_robot_parser)
            except:
                return False

        return self.dic_robots_per_domain[obj_url.netloc].can_fetch(self.usr_agent, obj_url.geturl())
