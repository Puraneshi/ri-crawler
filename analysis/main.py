from crawler.scheduler import Scheduler
from crawler.page_fetcher import PageFetcher
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import time

usr_agent = 'citycrawler (ricitycrawler.wordpress.com)'
page_limit = 100
depth_limit = 6
url_seeds = ['https://prefeitura.pbh.gov.br',
             'https://www.capital.sp.gov.br',
             'https://prefeitura.rio',
             'https://prefeitura.poa.br',
             'https://www.goiania.go.gov.br',
             'https://www.fortaleza.ce.gov.br',
             'https://www.curitiba.pr.gov.br',
             'http://www.belem.pa.gov.br',
             'https://www.df.gov.br',
             'https://www.saopaulo.sp.leg.br',
             'https://www.pmf.sc.gov.br',
             'https://www.natal.rn.gov.br',
             'https://boavista.rr.gov.br',
             'https://macae.rj.gov.br',
             'https://www.vitoria.es.gov.br/',
             'https://www.ibge.gov.br'
            ]
arr_url_seeds = []
for url in url_seeds:
    arr_url_seeds.append(urlparse(url))


time_coleta_n = []
num_threads_n = []

for n in range(1, 22, 5):
    thread_number = n
    obj_scheduler = Scheduler(usr_agent, page_limit, depth_limit, arr_url_seeds)

    start = time.time()

    arr_obj_fetcher = []
    for _ in range(thread_number):
        arr_obj_fetcher.append(PageFetcher(obj_scheduler))
        arr_obj_fetcher[-1].start()
    for thread in arr_obj_fetcher:
        thread.join()

    end = time.time()

    time_coleta_n.append(end-start)
    num_threads_n.append(n)

for n in range(30, 151, 20):
    thread_number = n
    obj_scheduler = Scheduler(usr_agent, page_limit, depth_limit, arr_url_seeds)

    start = time.time()

    arr_obj_fetcher = []
    for _ in range(thread_number):
        arr_obj_fetcher.append(PageFetcher(obj_scheduler))
        arr_obj_fetcher[-1].start()
    for thread in arr_obj_fetcher:
        thread.join()

    end = time.time()

    time_coleta_n.append(end - start)
    num_threads_n.append(n)

plt.plot(num_threads_n, time_coleta_n)
plt.show()