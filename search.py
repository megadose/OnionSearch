import argparse
import csv
import math
import re
import time
from datetime import datetime
from random import choice

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

desktop_agents = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) '
    'AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
]

supported_engines = [
    "ahmia",
    "torch",
    "darksearchio",
    "onionland",
    "notevil",
    "visitor",
    "darksearchenginer",
    "phobos",
    "onionsearchserver",
    "grams",
    "candle",
    "torsearchengine",
    "torgle",
    "onionsearchengine",
    "tordex",
    "tor66",
    "tormax",
    "haystack",
    "multivac",
    "evosearch",
    "oneirun",
    "deeplink",
]

available_csv_fields = [
    "engine",
    "name",
    "link",
    "domain"
    # Todo: add description, but needs modify scraping (link_finder func) for all the engines
]


def print_epilog():
    epilog = "Available CSV fields: \n\t"
    for f in available_csv_fields:
        epilog += " {}".format(f)
    epilog += "\n"
    epilog += "Supported engines: \n\t"
    for e in supported_engines:
        epilog += " {}".format(e)
    return epilog


parser = argparse.ArgumentParser(epilog=print_epilog(), formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument("--proxy", default='localhost:9050', type=str, help="Set Tor proxy (default: 127.0.0.1:9050)")
parser.add_argument("--output", default='output_$SEARCH_$DATE.txt', type=str,
                    help="Output File (default: output_$SEARCH_$DATE.txt), where $SEARCH is replaced by the first "
                         "chars of the search string and $DATE is replaced by the datetime")
parser.add_argument("--continuous_write", type=bool, default=False,
                    help="Write progressively to output file (default: False)")
parser.add_argument("search", type=str, help="The search string or phrase")
parser.add_argument("--limit", type=int, default=0, help="Set a max number of pages per engine to load")
parser.add_argument("--barmode", type=str, default="fixed", help="Can be 'fixed' (default) or 'unknown'")
parser.add_argument("--engines", type=str, action='append', help='Engines to request (default: full list)', nargs="*")
parser.add_argument("--exclude", type=str, action='append', help='Engines to exclude (default: none)', nargs="*")
parser.add_argument("--fields", type=str, action='append',
                    help='Fields to output to csv file (default: engine name link), available fields are shown below',
                    nargs="*")
parser.add_argument("--field_delimiter", type=str, default=",", help='Delimiter for the CSV fields')

args = parser.parse_args()
proxies = {'http': 'socks5h://{}'.format(args.proxy), 'https': 'socks5h://{}'.format(args.proxy)}
tqdm_bar_format = "{desc}: {percentage:3.0f}% |{bar}| {n_fmt:3s} / {total_fmt:3s} [{elapsed:5s} < {remaining:5s}]"
result = {}
filename = args.output
field_delim = ","
if args.field_delimiter and len(args.field_delimiter) == 1:
    field_delim = args.field_delimiter

def random_headers():
    return {'User-Agent': choice(desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


def clear(toclear):
    str = toclear.replace("\n", " ")
    str = ' '.join(str.split())
    return str


def ahmia(searchstr):
    ahmia_url = "http://msydqstlz2kzerdg.onion/search/?q={}"

    with tqdm(total=1, initial=0, desc="%20s" % "Ahmia", unit="req", ascii=False, ncols=120,
              bar_format=tqdm_bar_format) as progress_bar:
        response = requests.get(ahmia_url.format(searchstr), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(response.text, 'html.parser')
        link_finder("ahmia", soup)
        progress_bar.update()
        progress_bar.close()


def torch(searchstr):
    torch_url = "http://xmh57jrzrnw6insl.onion/4a1f6b371c/search.cgi?cmd=Search!&np={}&q={}"
    results_per_page = 10
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        req = s.get(torch_url.format(0, searchstr))
        soup = BeautifulSoup(req.text, 'html.parser')

        page_number = 1
        for i in soup.find("table", attrs={"width": "100%"}).find_all("small"):
            if i.get_text() is not None and "of" in i.get_text():
                page_number = math.ceil(float(clear(i.get_text().split("-")[1].split("of")[1])) / results_per_page)
                if page_number > max_nb_page:
                    page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "TORCH", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("torch", soup)
            progress_bar.update()

            # Usually range is 2 to n+1, but TORCH behaves differently
            for n in range(1, page_number):
                req = s.get(torch_url.format(n, searchstr))
                soup = BeautifulSoup(req.text, 'html.parser')
                link_finder("torch", soup)
                progress_bar.update()

            progress_bar.close()


def darksearchio(searchstr):
    global result
    result['darksearchio'] = []
    darksearchio_url = "http://darksearch.io/api/search?query={}&page={}"
    max_nb_page = 30
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()
        resp = s.get(darksearchio_url.format(searchstr, 1))

        page_number = 1
        if resp.status_code == 200:
            resp = resp.json()
            if 'last_page' in resp:
                page_number = resp['last_page']
            if page_number > max_nb_page:
                page_number = max_nb_page
        else:
            return

        with tqdm(total=page_number, initial=0, desc="%20s" % "DarkSearch (.io)", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("darksearchio", resp['data'])
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(darksearchio_url.format(searchstr, n))
                if resp.status_code == 200:
                    resp = resp.json()
                    link_finder("darksearchio", resp['data'])
                    progress_bar.update()
                else:
                    # Current page results will be lost but we will try to continue after a short sleep
                    time.sleep(1)

            progress_bar.close()


def onionland(searchstr):
    onionlandv3_url = "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion/search?q={}&page={}"
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(onionlandv3_url.format(searchstr, 1))
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_number = 1
        for i in soup.find_all('div', attrs={"class": "search-status"}):
            approx_re = re.match(r"About ([,0-9]+) result(.*)",
                                 clear(i.find('div', attrs={'class': "col-sm-12"}).get_text()))
            if approx_re is not None:
                nb_res = int((approx_re.group(1)).replace(",", ""))
                results_per_page = 19
                page_number = math.ceil(nb_res / results_per_page)
                if page_number > max_nb_page:
                    page_number = max_nb_page

        bar_max = None
        if args.barmode == "fixed":
            bar_max = max_nb_page

        with tqdm(total=bar_max, initial=0, desc="%20s" % "OnionLand", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("onionland", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(onionlandv3_url.format(searchstr, n))
                soup = BeautifulSoup(resp.text, 'html.parser')
                ret = link_finder("onionland", soup)
                if ret < 0:
                    break
                progress_bar.update()

            progress_bar.close()


def notevil(searchstr):
    notevil_url1 = "http://hss3uro2hsxfogfq.onion/index.php?q={}"
    notevil_url2 = "http://hss3uro2hsxfogfq.onion/index.php?q={}&hostLimit=20&start={}&numRows={}&template=0"
    max_nb_page = 20
    if args.limit != 0:
        max_nb_page = args.limit

    # Do not use requests.Session() here (by experience less results would be got)
    req = requests.get(notevil_url1.format(searchstr), proxies=proxies, headers=random_headers())
    soup = BeautifulSoup(req.text, 'html.parser')

    page_number = 1
    last_div = soup.find("div", attrs={"style": "text-align:center"}).find("div", attrs={"style": "text-align:center"})
    if last_div is not None:
        for i in last_div.find_all("a"):
            page_number = int(i.get_text())
        if page_number > max_nb_page:
            page_number = max_nb_page

    num_rows = 20
    with tqdm(total=page_number, initial=0, desc="%20s" % "not Evil", unit="req", ascii=False, ncols=120,
              bar_format=tqdm_bar_format) as progress_bar:

        link_finder("notevil", soup)
        progress_bar.update()

        for n in range(2, page_number + 1):
            start = (int(n - 1) * num_rows)
            req = requests.get(notevil_url2.format(searchstr, start, num_rows),
                               proxies=proxies,
                               headers=random_headers())
            soup = BeautifulSoup(req.text, 'html.parser')
            link_finder("notevil", soup)
            progress_bar.update()
            time.sleep(1)

        progress_bar.close()


def visitor(searchstr):
    visitor_url = "http://visitorfi5kl7q7i.onion/search/?q={}&page={}"
    max_nb_page = 30
    if args.limit != 0:
        max_nb_page = args.limit

    bar_max = None
    if args.barmode == "fixed":
        bar_max = max_nb_page
    with tqdm(total=bar_max, initial=0, desc="%20s" % "VisiTOR", unit="req", ascii=False, ncols=120,
              bar_format=tqdm_bar_format) as progress_bar:

        continue_processing = True
        page_to_request = 1

        with requests.Session() as s:
            s.proxies = proxies
            s.headers = random_headers()

            while continue_processing:
                resp = s.get(visitor_url.format(searchstr, page_to_request))
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("visitor", soup)
                progress_bar.update()

                next_page = soup.find('a', text="Next »")
                if next_page is None or page_to_request >= max_nb_page:
                    continue_processing = False

                page_to_request += 1

            progress_bar.close()


def darksearchenginer(searchstr):
    darksearchenginer_url = "http://7pwy57iklvt6lyhe.onion/"
    max_nb_page = 20
    if args.limit != 0:
        max_nb_page = args.limit
    page_number = 1

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        # Note that this search engine is very likely to timeout
        resp = s.post(darksearchenginer_url, data={"search[keyword]": searchstr, "page": page_number})
        soup = BeautifulSoup(resp.text, 'html.parser')

        pages_input = soup.find_all("input", attrs={"name": "page"})
        for i in pages_input:
            page_number = int(i['value'])
            if page_number > max_nb_page:
                page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Dark Search Enginer", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("darksearchenginer", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.post(darksearchenginer_url, data={"search[keyword]": searchstr, "page": str(n)})
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("darksearchenginer", soup)
                progress_bar.update()

            progress_bar.close()


def phobos(searchstr):
    phobos_url = "http://phobosxilamwcg75xt22id7aywkzol6q6rfl2flipcqoc4e4ahima5id.onion/search?query={}&p={}"
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(phobos_url.format(searchstr, 1), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_number = 1
        pages = soup.find("div", attrs={"class": "pages"}).find_all('a')
        if pages is not None:
            for i in pages:
                page_number = int(i.get_text())
            if page_number > max_nb_page:
                page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Phobos", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("phobos", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(phobos_url.format(searchstr, n), proxies=proxies, headers=random_headers())
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("phobos", soup)
                progress_bar.update()

            progress_bar.close()


def onionsearchserver(searchstr):
    onionsearchserver_url1 = "http://oss7wrm7xvoub77o.onion/oss/"
    onionsearchserver_url2 = None
    results_per_page = 10
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(onionsearchserver_url1)
        soup = BeautifulSoup(resp.text, 'html.parser')
        for i in soup.find_all('iframe', attrs={"style": "display:none;"}):
            onionsearchserver_url2 = i['src'] + "{}&page={}"

        if onionsearchserver_url2 is None:
            return -1

        resp = s.get(onionsearchserver_url2.format(searchstr, 1))
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_number = 1
        pages = soup.find_all("div", attrs={"class": "osscmnrdr ossnumfound"})
        if pages is not None and not str(pages[0].get_text()).startswith("No"):
            total_results = float(str.split(clear(pages[0].get_text()))[0])
            page_number = math.ceil(total_results / results_per_page)
            if page_number > max_nb_page:
                page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Onion Search Server", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("onionsearchserver", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(onionsearchserver_url2.format(searchstr, n))
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("onionsearchserver", soup)
                progress_bar.update()

            progress_bar.close()


def grams(searchstr):
    # No multi pages handling as it is very hard to get many results on this engine
    grams_url1 = "http://grams7enqfy4nieo.onion/"
    grams_url2 = "http://grams7enqfy4nieo.onion/results"

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(grams_url1)
        soup = BeautifulSoup(resp.text, 'html.parser')
        token = soup.find('input', attrs={'name': '_token'})['value']

        with tqdm(total=1, initial=0, desc="%20s" % "Grams", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:
            resp = s.post(grams_url2, data={"req": searchstr, "_token": token})
            soup = BeautifulSoup(resp.text, 'html.parser')
            link_finder("grams", soup)
            progress_bar.update()
            progress_bar.close()


def candle(searchstr):
    candle_url = "http://gjobjn7ievumcq6z.onion/?q={}"

    with tqdm(total=1, initial=0, desc="%20s" % "Candle", unit="req", ascii=False, ncols=120,
              bar_format=tqdm_bar_format) as progress_bar:
        response = requests.get(candle_url.format(searchstr), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(response.text, 'html.parser')
        link_finder("candle", soup)
        progress_bar.update()
        progress_bar.close()


def torsearchengine(searchstr):
    torsearchengine_url = "http://searchcoaupi3csb.onion/search/move/?q={}&pn={}&num=10&sdh=&"
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(torsearchengine_url.format(searchstr, 1))
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_number = 1
        for i in soup.find_all('div', attrs={"id": "subheader"}):
            if i.get_text() is not None and "of" in i.get_text():
                total_results = int(i.find('p').find_all('b')[2].get_text().replace(",", ""))
                results_per_page = 10
                page_number = math.ceil(total_results / results_per_page)
                if page_number > max_nb_page:
                    page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Tor Search Engine", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("torsearchengine", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(torsearchengine_url.format(searchstr, n))
                soup = BeautifulSoup(resp.text, 'html.parser')
                ret = link_finder("torsearchengine", soup)
                progress_bar.update()

            progress_bar.close()


def torgle(searchstr):
    torgle_url = "http://torglejzid2cyoqt.onion/search.php?term={}"

    with tqdm(total=1, initial=0, desc="%20s" % "Torgle", unit="req", ascii=False, ncols=120,
              bar_format=tqdm_bar_format) as progress_bar:
        response = requests.get(torgle_url.format(searchstr), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(response.text, 'html.parser')
        link_finder("torgle", soup)
        progress_bar.update()
        progress_bar.close()


def onionsearchengine(searchstr):
    onionsearchengine_url = "http://onionf4j3fwqpeo5.onion/search.php?search={}&submit=Search&page={}"
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(onionsearchengine_url.format(searchstr, 1))
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_number = 1
        approx_re = re.search(r"\s([0-9]+)\sresult[s]?\sfound\s!.*", clear(soup.find('body').get_text()))
        if approx_re is not None:
            nb_res = int(approx_re.group(1))
            results_per_page = 9
            page_number = math.ceil(float(nb_res / results_per_page))
            if page_number > max_nb_page:
                page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Onion Search Engine", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("onionsearchengine", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(onionsearchengine_url.format(searchstr, n))
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("onionsearchengine", soup)
                progress_bar.update()

            progress_bar.close()


def tordex(searchstr):
    tordex_url = "http://tordex7iie7z2wcg.onion/search?query={}&page={}"
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(tordex_url.format(searchstr, 1))
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_number = 1
        pages = soup.find_all("li", attrs={"class": "page-item"})
        if pages is not None:
            for i in pages:
                if i.get_text() != "...":
                    page_number = int(i.get_text())
            if page_number > max_nb_page:
                page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Tordex", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("tordex", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(tordex_url.format(searchstr, n))
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("tordex", soup)
                progress_bar.update()

            progress_bar.close()


def tor66(searchstr):
    tor66_url = "http://tor66sezptuu2nta.onion/search?q={}&sorttype=rel&page={}"
    max_nb_page = 30
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(tor66_url.format(searchstr, 1))
        soup = BeautifulSoup(resp.text, 'html.parser')

        page_number = 1
        approx_re = re.search(r"\.Onion\ssites\sfound\s:\s([0-9]+)",
                              resp.text)
        if approx_re is not None:
            nb_res = int(approx_re.group(1))
            results_per_page = 20
            page_number = math.ceil(float(nb_res / results_per_page))
            if page_number > max_nb_page:
                page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Tor66", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("tor66", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(tor66_url.format(searchstr, n))
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("tor66", soup)
                progress_bar.update()

            progress_bar.close()


def tormax(searchstr):
    tormax_url = "http://tormaxunodsbvtgo.onion/tormax/search?q={}"

    with tqdm(total=1, initial=0, desc="%20s" % "Tormax", unit="req", ascii=False, ncols=120,
              bar_format=tqdm_bar_format) as progress_bar:
        response = requests.get(tormax_url.format(searchstr), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(response.text, 'html.parser')
        link_finder("tormax", soup)
        progress_bar.update()
        progress_bar.close()


def haystack(searchstr):
    haystack_url = "http://haystakvxad7wbk5.onion/?q={}&offset={}"
    # At the 52nd page, it timeouts 100% of the time
    max_nb_page = 50
    if args.limit != 0:
        max_nb_page = args.limit
    offset_coeff = 20

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        req = s.get(haystack_url.format(searchstr, 0))
        soup = BeautifulSoup(req.text, 'html.parser')

        bar_max = None
        if args.barmode == "fixed":
            bar_max = max_nb_page
        with tqdm(total=bar_max, initial=0, desc="%20s" % "Haystack", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            continue_processing = True

            ret = link_finder("haystack", soup)
            if ret < 0:
                continue_processing = False
            progress_bar.update()

            it = 1
            while continue_processing:
                offset = int(it * offset_coeff)
                req = s.get(haystack_url.format(searchstr, offset))
                soup = BeautifulSoup(req.text, 'html.parser')
                ret = link_finder("haystack", soup)
                progress_bar.update()
                it += 1
                if it >= max_nb_page or ret < 0:
                    continue_processing = False


def multivac(searchstr):
    multivac_url = "http://multivacigqzqqon.onion/?q={}&page={}"
    max_nb_page = 10
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        page_to_request = 1
        req = s.get(multivac_url.format(searchstr, page_to_request))
        soup = BeautifulSoup(req.text, 'html.parser')

        bar_max = None
        if args.barmode == "fixed":
            bar_max = max_nb_page
        with tqdm(total=bar_max, initial=0, desc="%20s" % "Multivac", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            continue_processing = True

            ret = link_finder("multivac", soup)
            if ret < 0 or page_to_request >= max_nb_page:
                continue_processing = False
            progress_bar.update()

            while continue_processing:
                page_to_request += 1
                req = s.get(multivac_url.format(searchstr, page_to_request))
                soup = BeautifulSoup(req.text, 'html.parser')
                ret = link_finder("multivac", soup)
                progress_bar.update()

                if page_to_request >= max_nb_page or ret < 0:
                    continue_processing = False


def evosearch(searchstr):
    evosearch_url = "http://evo7no6twwwrm63c.onion/evo/search.php?" \
                    "query={}&" \
                    "start={}&" \
                    "search=1&type=and&mark=bold+text&" \
                    "results={}"
    results_per_page = 50
    max_nb_page = 30
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        req = s.get(evosearch_url.format(searchstr, 1, results_per_page))
        soup = BeautifulSoup(req.text, 'html.parser')

        page_number = 1
        i = soup.find("p", attrs={"class": "cntr"})
        if i is not None:
            if i.get_text() is not None and "of" in i.get_text():
                nb_res = float(clear(str.split(i.get_text().split("-")[1].split("of")[1])[0]))
                # The results page loads in two times, it is hard not to lose the second part
                page_number = math.ceil(nb_res / (results_per_page / 2))
                if page_number > max_nb_page:
                    page_number = max_nb_page

        with tqdm(total=page_number, initial=0, desc="%20s" % "Evo Search", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:

            link_finder("evosearch", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(evosearch_url.format(searchstr, n, results_per_page))
                soup = BeautifulSoup(resp.text, 'html.parser')
                link_finder("evosearch", soup)
                progress_bar.update()

            progress_bar.close()


def oneirun(searchstr):
    oneirun_url = "http://oneirunda366dmfm.onion/Home/IndexEn"

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(oneirun_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        token = soup.find('input', attrs={"name": "__RequestVerificationToken"})['value']

        with tqdm(total=1, initial=0, desc="%20s" % "Oneirun", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:
            response = s.post(oneirun_url.format(searchstr),
                              data={"searchString": searchstr, "__RequestVerificationToken": token})
            soup = BeautifulSoup(response.text, 'html.parser')
            link_finder("oneirun", soup)
            progress_bar.update()
            progress_bar.close()


def deeplink(searchstr):
    deeplink_url1 = "http://deeplinkdeatbml7.onion/index.php"
    deeplink_url2 = "http://deeplinkdeatbml7.onion/?search={}&type=verified"

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()
        resp = s.get(deeplink_url1)

        with tqdm(total=1, initial=0, desc="%20s" % "DeepLink", unit="req", ascii=False, ncols=120,
                  bar_format=tqdm_bar_format) as progress_bar:
            response = s.get(deeplink_url2.format(searchstr))
            soup = BeautifulSoup(response.text, 'html.parser')
            link_finder("deeplink", soup)
            progress_bar.update()
            progress_bar.close()


def get_domain_from_url(link):
    fqdn_re = r"^[a-z][a-z0-9+\-.]*://([a-z0-9\-._~%!$&'()*+,;=]+@)?([a-z0-9\-._~%]+|\[[a-z0-9\-._~%!$&'()*+,;=:]+\])"
    domain_re = re.match(fqdn_re, link)
    if domain_re is not None:
        if domain_re.lastindex == 2:
            return domain_re.group(2)
    return None


def write_to_csv(csv_writer, fields):
    line_to_write = []
    if args.fields and len(args.fields) > 0:
        for f in args.fields[0]:
            if f in fields:
                line_to_write.append(fields[f])
            if f == "domain":
                domain = get_domain_from_url(fields['link'])
                line_to_write.append(domain)
        csv_writer.writerow(line_to_write)
    else:
        # Default output mode
        line_to_write.append(fields['engine'])
        line_to_write.append(fields['name'])
        line_to_write.append(fields['link'])
        csv_writer.writerow(line_to_write)


def link_finder(engine_str, data_obj):
    global result
    global filename
    name = ""
    link = ""
    csv_file = None
    has_result = False

    if args.continuous_write:
        csv_file = open(filename, 'a', newline='')

    def append_link():
        nonlocal has_result
        has_result = True

        result[engine_str].append({"name": name, "link": link})

        if args.continuous_write and csv_file.writable():
            csv_writer = csv.writer(csv_file, delimiter=field_delim, quoting=csv.QUOTE_NONNUMERIC)
            fields = {"engine": engine_str, "name": name, "link": link}
            write_to_csv(csv_writer, fields)

    if engine_str not in result:
        result[engine_str] = []

    if engine_str == "ahmia":
        for i in data_obj.find_all('li', attrs={'class': 'result'}):
            i = i.find('h4')
            name = clear(i.get_text())
            link = i.find('a')['href'].replace("/search/search/redirect?search_term={}&redirect_url="
                                               .format(args.search), "")
            append_link()

    if engine_str == "candle":
        html_page = data_obj.find('html')
        if html_page:
            for i in data_obj.find('html').find_all('a'):
                if str(i['href']).startswith("http"):
                    name = clear(i.get_text())
                    link = clear(i['href'])
                    append_link()

    if engine_str == "darksearchenginer":
        for i in data_obj.find('div', attrs={"class": "table-responsive"}).find_all('a'):
            name = clear(i.get_text())
            link = clear(i['href'])
            append_link()

    if engine_str == "darksearchio":
        for r in data_obj:
            name = clear(r["title"])
            link = clear(r["link"])
            append_link()

    if engine_str == "deeplink":
        for tr in data_obj.find_all('tr'):
            cels = tr.find_all('td')
            if cels is not None and len(cels) == 4:
                name = clear(cels[1].get_text())
                link = clear(cels[0].find('a')['href'])
                append_link()

    if engine_str == "evosearch":
        if data_obj.find('div', attrs={"id": "results"}) is not None:
            for div in data_obj.find('div', attrs={"id": "results"}).find_all('div', attrs={"class": "odrow"}):
                name = clear(div.find('div', attrs={"class": "title"}).find('a').get_text())
                link = clear(div.find('div', attrs={"class": "title"}).find('a')['href']
                             .replace("./include/click_counter.php?url=", "")
                             .replace("&query={}".format(args.search), ""))
                append_link()

    if engine_str == "grams":
        for i in data_obj.find_all("div", attrs={"class": "media-body"}):
            if not i.find('span'):
                for j in i.find_all('a'):
                    if str(j.get_text()).startswith("http"):
                        link = j.get_text()
                    else:
                        name = j.get_text()
                append_link()

    if engine_str == "haystack":
        if data_obj.find('div', attrs={"class": "result"}) is not None:
            for div in data_obj.find_all('div', attrs={"class": "result"}):
                if div.find('a') is not None and div.find('i') is not None:
                    name = clear(div.find('a').get_text())
                    link = clear(div.find('i').get_text())
                    append_link()

    if engine_str == "multivac":
        for i in data_obj.find_all('dl'):
            link_tag = i.find('a')
            if link_tag:
                if link_tag['href'] != "":
                    name = clear(link_tag.get_text())
                    link = clear(link_tag['href'])
                    append_link()
                else:
                    break

    if engine_str == "notevil":
        ''' As for OnionLand, we could use the span instead of the href to get a beautiful link
            However some useful links are shown under the "li" tag,
            and there we would not be able to have a sanitized version
            Thus, the best is to implement a generic sanitize function. '''
        for i in data_obj.find_all('p'):
            name = clear(i.find('a').get_text())
            link = i.find('a')['href'].replace("./r2d.php?url=", "")
            append_link()
        for i in data_obj.find_all('li'):
            name = clear(i.find('a').get_text())
            link = i.find('a')['href'].replace("./r2d.php?url=", "")
            append_link()

    if engine_str == "oneirun":
        for td in data_obj.find_all('td', attrs={"style": "vertical-align: top;"}):
            name = clear(td.find('h5').get_text())
            link = clear(td.find('a')['href'])
            append_link()

    if engine_str == "onionland":
        if not data_obj.find('div', attrs={"class": "row no-result-row"}):
            for i in data_obj.find_all('div', attrs={"class": "result-block"}):
                if not str(clear(i.find('div', attrs={'class': "title"}).find('a')['href'])).startswith("/ads"):
                    name = clear(i.find('div', attrs={'class': "title"}).get_text())
                    link = clear(i.find('div', attrs={'class': "link"}).get_text())
                    append_link()

    if engine_str == "onionsearchengine":
        for i in data_obj.find_all('table'):
            for j in i.find_all('a'):
                if str(j['href']).startswith("url.php?u=") and not str(j.get_text()).startswith("http://"):
                    name = clear(j.get_text())
                    link = clear(str(j['href']).replace("url.php?u=", ""))
                    append_link()

    if engine_str == "onionsearchserver":
        for i in data_obj.find_all('div', attrs={"class": "osscmnrdr ossfieldrdr1"}):
            name = clear(i.find('a').get_text())
            link = clear(i.find('a')['href'])
            append_link()

    if engine_str == "phobos":
        links = data_obj.find('div', attrs={"class": "serp"}).find_all('a', attrs={"class": "titles"})
        for i in links:
            name = clear(i.get_text())
            link = clear(i['href'])
            append_link()

    if engine_str == "tor66":
        for i in data_obj.find('hr').find_all_next('b'):
            if i.find('a'):
                name = clear(i.find('a').get_text())
                link = clear(i.find('a')['href'])
                append_link()

    if engine_str == "torch":
        for i in data_obj.find_all('dl'):
            name = clear(i.find('a').get_text())
            link = i.find('a')['href']
            append_link()

    if engine_str == "tordex":
        for i in data_obj.find_all('div', attrs={"class": "result mb-3"}):
            a_link = i.find('h5').find('a')
            name = clear(a_link.get_text())
            link = clear(a_link['href'])
            append_link()

    if engine_str == "torgle":
        for i in data_obj.find_all('ul', attrs={"id": "page"}):
            for j in i.find_all('a'):
                if str(j.get_text()).startswith("http"):
                    link = clear(j.get_text())
                else:
                    name = clear(j.get_text())
            append_link()

    if engine_str == "tormax":
        for i in data_obj.find_all('article'):
            if i.find('a') is not None and i.find('div') is not None:
                link = clear(i.find('div', attrs={"class": "url"}).get_text())
                name = clear(i.find('a', attrs={"class": "title"}).get_text())
                append_link()

    if engine_str == "torsearchengine":
        for i in data_obj.find_all('h3', attrs={'class': 'title text-truncate'}):
            name = clear(i.find('a').get_text())
            link = i.find('a')['data-uri']
            append_link()

    if engine_str == "visitor":
        li_tags = data_obj.find_all('li', attrs={'class': 'hs_site'})
        for i in li_tags:
            h3tags = i.find_all('h3')
            for n in h3tags:
                name = clear(n.find('a').get_text())
                link = n.find('a')['href']
                append_link()

    if args.continuous_write and not csv_file.closed:
        csv_file.close()

    if not has_result:
        return -1

    return 1


def call_func_as_str(function_name, function_arg):
    try:
        globals()[function_name](function_arg)
    except ConnectionError:
        print("Error: unable to connect")
    except OSError:
        print("Error: unable to connect")


def scrape():
    global result
    global filename

    start_time = datetime.now()

    # Building the filename
    filename = str(filename).replace("$DATE", start_time.strftime("%Y%m%d%H%M%S"))
    search = str(args.search).replace(" ", "")
    if len(search) > 10:
        search = search[0:9]
    filename = str(filename).replace("$SEARCH", search)

    if args.engines and len(args.engines) > 0:
        engines = args.engines[0]
        for e in engines:
            try:
                if not (args.exclude and len(args.exclude) > 0 and e in args.exclude[0]):
                    call_func_as_str(e, args.search)
            except KeyError:
                print("Error: search engine {} not in the list of supported engines".format(e))
    else:
        for e in supported_engines:
            if not (args.exclude and len(args.exclude) > 0 and e in args.exclude[0]):
                call_func_as_str(e, args.search)

    stop_time = datetime.now()

    if not args.continuous_write:
        with open(filename, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=field_delim, quoting=csv.QUOTE_NONNUMERIC)
            for engine in result.keys():
                for i in result[engine]:
                    i['engine'] = engine
                    write_to_csv(csv_writer, i)

    total = 0
    print("\nReport:")
    print("  Execution time: %s seconds" % (stop_time - start_time))
    for engine in result.keys():
        print("  {}: {}".format(engine, str(len(result[engine]))))
        total += len(result[engine])
    print("  Total: {} links written to {}".format(str(total), filename))


if __name__ == "__main__":
    scrape()
