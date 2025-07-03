#!/usr/bin/python3

import argparse
import csv
import math
import re
import time
from datetime import datetime
from functools import reduce
from random import choice
from multiprocessing import Pool, cpu_count, current_process, freeze_support
from tqdm import tqdm

import requests
import urllib.parse as urlparse
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import unquote
from bs4 import BeautifulSoup
from urllib3.exceptions import ProtocolError

ENGINES = {
    "ahmia": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion", 
    "onionland": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion",
    "onionsearchserver": "http://3fzh7yuupdfyjhwt3ugzqqof6ulbcl27ecev33knxe3u7goi3vfn2qqd.onion",
    "torgle": "http://no6m4wzdexe3auiupv2zwif7rm6qwxcyhslkcnzisxgeiw6pvjsgafad.onion",  # "torgle" -> "Submarine"
    "tor66": "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion",
    "haystack": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion",
    "torch": "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion"

}

desktop_agents = [
    'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0',  # Tor Browser for Windows and Linux
    'Mozilla/5.0 (Android 10; Mobile; rv:91.0) Gecko/91.0 Firefox/91.0',  # Tor Browser for Android
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

supported_engines = ENGINES

available_csv_fields = [
    "engine",
    "name",
    "link",
    "domain"
]


def print_epilog():
    epilog = "Available CSV fields: \n\t"
    for f in available_csv_fields:
        epilog += " {}".format(f)
    epilog += "\n"
    epilog += "Supported engines: \n\t"
    for e in supported_engines.keys():
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
parser.add_argument("--engines", type=str, action='append', help='Engines to request (default: full list)', nargs="*")
parser.add_argument("--exclude", type=str, action='append', help='Engines to exclude (default: none)', nargs="*")
parser.add_argument("--fields", type=str, action='append',
                    help='Fields to output to csv file (default: engine name link), available fields are shown below',
                    nargs="*")
parser.add_argument("--field_delimiter", type=str, default=",", help='Delimiter for the CSV fields')
parser.add_argument("--mp_units", type=int, default=(cpu_count() - 1), help="Number of processing units (default: "
                                                                            "core number minus 1)")

args = parser.parse_args()
proxies = {'http': 'socks5h://{}'.format(args.proxy), 'https': 'socks5h://{}'.format(args.proxy)}
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


def get_parameter(url, parameter_name):
    parsed = urlparse.urlparse(url)
    return parse_qs(parsed.query)[parameter_name][0]


def get_proc_pos():
    return (current_process()._identity[0]) - 1


def get_tqdm_desc(e_name, pos):
    return "%20s (#%d)" % (e_name, pos)


def ahmia(searchstr):
    results = []
    ahmia_url = supported_engines['ahmia'] + "/search/?q={}"

    pos = get_proc_pos()
    with tqdm(total=1, initial=0, desc=get_tqdm_desc("Ahmia", pos), position=pos) as progress_bar:
        response = requests.get(ahmia_url.format(quote(searchstr)), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(response.text, 'html5lib')
        results = link_finder("ahmia", soup)
        progress_bar.update()

    return results


def onionland(searchstr):
    results = []
    onionlandv3_url = supported_engines['onionland'] + "/search?q={}&page={}"
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(onionlandv3_url.format(quote(searchstr), 1))
        soup = BeautifulSoup(resp.text, 'html5lib')

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

        pos = get_proc_pos()
        with tqdm(total=max_nb_page, initial=0, desc=get_tqdm_desc("OnionLand", pos), position=pos) as progress_bar:

            results = link_finder("onionland", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(onionlandv3_url.format(quote(searchstr), n))
                soup = BeautifulSoup(resp.text, 'html5lib')
                ret = link_finder("onionland", soup)
                if len(ret) == 0:
                    break
                results = results + ret
                progress_bar.update()

    return results


def onionsearchserver(searchstr):
    results = []
    onionsearchserver_url1 = supported_engines['onionsearchserver'] + "/oss/"
    onionsearchserver_url2 = None
    results_per_page = 10
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(onionsearchserver_url1)
        soup = BeautifulSoup(resp.text, 'html5lib')
        for i in soup.find_all('iframe', attrs={"style": "display:none;"}):
            onionsearchserver_url2 = i['src'] + "{}&page={}"

        if onionsearchserver_url2 is None:
            return results

        resp = s.get(onionsearchserver_url2.format(quote(searchstr), 1))
        soup = BeautifulSoup(resp.text, 'html5lib')

        page_number = 1
        pages = soup.find_all("div", attrs={"class": "osscmnrdr ossnumfound"})
        if pages is not None and not str(pages[0].get_text()).startswith("No"):
            total_results = float(str.split(clear(pages[0].get_text()))[0])
            page_number = math.ceil(total_results / results_per_page)
            if page_number > max_nb_page:
                page_number = max_nb_page

        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Onion Search Server", pos), position=pos) \
                as progress_bar:

            results = link_finder("onionsearchserver", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(onionsearchserver_url2.format(quote(searchstr), n))
                soup = BeautifulSoup(resp.text, 'html5lib')
                results = results + link_finder("onionsearchserver", soup)
                progress_bar.update()

    return results



def torgle(searchstr):
    results = []
    torgle_url = supported_engines['torgle'] + "/search.php?term={}"

    pos = get_proc_pos()
    with tqdm(total=1, initial=0, desc=get_tqdm_desc("Torgle", pos), position=pos) as progress_bar:
        response = requests.get(torgle_url.format(quote(searchstr)), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(response.text, 'html5lib')
        results = link_finder("torgle", soup)
        progress_bar.update()

    return results


def tor66(searchstr):
    results = []
    tor66_url = supported_engines['tor66'] + "/search?q={}&sorttype=rel&page={}"
    max_nb_page = 30
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(tor66_url.format(quote(searchstr), 1))
        soup = BeautifulSoup(resp.text, 'html5lib')

        page_number = 1
        approx_re = re.search(r"\.Onion\ssites\sfound\s:\s([0-9]+)", resp.text)
        if approx_re is not None:
            nb_res = int(approx_re.group(1))
            results_per_page = 20
            page_number = math.ceil(float(nb_res / results_per_page))
            if page_number > max_nb_page:
                page_number = max_nb_page

        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Tor66", pos), position=pos) as progress_bar:

            results = link_finder("tor66", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(tor66_url.format(quote(searchstr), n))
                soup = BeautifulSoup(resp.text, 'html5lib')
                results = results + link_finder("tor66", soup)
                progress_bar.update()

    return results


def haystack(searchstr):
    results = []
    haystack_url = supported_engines['haystack'] + "/?q={}&offset={}"
    # At the 52nd page, it timeouts 100% of the time
    max_nb_page = 50
    if args.limit != 0:
        max_nb_page = args.limit
    offset_coeff = 20

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        req = s.get(haystack_url.format(quote(searchstr), 0))
        soup = BeautifulSoup(req.text, 'html5lib')

        pos = get_proc_pos()
        with tqdm(total=max_nb_page, initial=0, desc=get_tqdm_desc("Haystack", pos), position=pos) as progress_bar:
            continue_processing = True
            ret = link_finder("haystack", soup)
            results = results + ret
            progress_bar.update()
            if len(ret) == 0:
                continue_processing = False

            it = 1
            while continue_processing:
                offset = int(it * offset_coeff)
                req = s.get(haystack_url.format(quote(searchstr), offset))
                soup = BeautifulSoup(req.text, 'html5lib')
                ret = link_finder("haystack", soup)
                results = results + ret
                progress_bar.update()
                it += 1
                if it >= max_nb_page or len(ret) == 0:
                    continue_processing = False

    return results


def torch(searchStr):
    results = []
    torch_url = supported_engines['torch'] + "/cgi-bin/omega/omega?P={}&%5B={}"
    max_nb_page = 100
    if args.limit != 0:
        max_nb_page = args.limit

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(torch_url.format(quote(searchStr), 1), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(resp.text, 'html5lib')

        page_number = 1
        matches = soup.find("center").get_text().split('\n')
        for m in matches:
            if 'No documents match' not in m:
                if 'matches' in m:
                    word = m.strip().split(' ')
                    last = word[-2]

                    page_number = math.ceil(float(last.replace(',', ''))/10)
                    if page_number > max_nb_page:
                        page_number = max_nb_page
            else:
                return results

        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Torch", pos), position=pos) as progress_bar:
            results = link_finder("torch", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(torch_url.format(quote(searchStr), n), proxies=proxies, headers=random_headers())
                soup = BeautifulSoup(resp.text, 'html5lib')
                results = results + link_finder("torch", soup)
                progress_bar.update()

    return results


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
    global filename
    name = ""
    link = ""
    csv_file = None
    found_links = []

    if args.continuous_write:
        csv_file = open(filename, 'a', newline='')

    def add_link():
        found_links.append({"engine": engine_str, "name": name, "link": link})

        if args.continuous_write and csv_file.writable():
            csv_writer = csv.writer(csv_file, delimiter=field_delim, quoting=csv.QUOTE_ALL)
            fields = {"engine": engine_str, "name": name, "link": link}
            write_to_csv(csv_writer, fields)

    if engine_str == "ahmia":
        for r in data_obj.select('li.result h4'):
            name = clear(r.get_text())
            link = r.find('a')['href'].split('redirect_url=')[1]
            add_link()

    if engine_str == "onionland":
        for r in data_obj.find_all("div", class_="result-block"):
            a_tag = r.find("a", {"data-category": "text-result"})
            if a_tag:
                name = r.find("div", class_="title").get_text(strip=True)
                link = r.find("div", class_="link").get_text(strip=True)
                add_link()

    if engine_str == "onionsearchserver":
        for r in data_obj.select('.osscmnrdr.ossfieldrdr1 a'):
            name = clear(r.get_text())
            link = clear(r['href'])
            add_link()

    if engine_str == "torgle":
        for i in data_obj.find_all('ul', attrs={"id": "page"}):
            for j in i.find_all('a'):
                if str(j.get_text()).startswith("http"):
                    link = clear(j.get_text())
                else:
                    name = clear(j.get_text())
            add_link()

    if engine_str == "tor66":
        for i in data_obj.find('hr').find_all_next('b'):
            if i.find('a'):
                name = clear(i.find('a').get_text())
                link = clear(i.find('a')['href'])
                add_link()

    if engine_str == "haystack":
        for r in data_obj.select(".result b a"):
            name = clear(r.get_text())
            link = get_parameter(r['href'], 'url')
            add_link()

    if engine_str == "torch":
        for r in data_obj.find_all("tr"):
            td = r.find_all("td")[1].find("b").find("a")
            name = clear(td.get_text())
            link = td['href']
            add_link()

    if args.continuous_write and not csv_file.closed:
        csv_file.close()

    return found_links


def run_method(method_name_and_argument):
    method_name = method_name_and_argument.split(':')[0]
    argument = method_name_and_argument.split(':')[1]
    ret = []
    try:
        ret = globals()[method_name](argument)
    except Exception as e:
        print(f'Exception occured: {e}')
    return ret


def scrape():
    global filename

    start_time = datetime.now()

    # Building the filename
    filename = str(filename).replace("$DATE", start_time.strftime("%Y%m%d%H%M%S"))
    search = str(args.search).replace(" ", "")
    if len(search) > 10:
        search = search[0:9]
    filename = str(filename).replace("$SEARCH", search)

    func_args = []
    stats_dict = {}
    if args.engines and len(args.engines) > 0:
        eng = args.engines[0]
        for e in eng:
            try:
                if not (args.exclude and len(args.exclude) > 0 and e in args.exclude[0]):
                    func_args.append("{}:{}".format(e, args.search))
                    stats_dict[e] = 0
            except KeyError:
                print("Error: search engine {} not in the list of supported engines".format(e))
    else:
        for e in supported_engines.keys():
            if not (args.exclude and len(args.exclude) > 0 and e in args.exclude[0]):
                func_args.append("{}:{}".format(e, args.search))
                stats_dict[e] = 0

    # Doing multiprocessing
    if args.mp_units and args.mp_units > 0:
        units = args.mp_units
    else:
        # Use (cores count - 1), but not less then one, threads
        units = max((cpu_count() - 1), 1)
    print("search.py started with {} processing units...".format(units))
    freeze_support()

    results = {}
    with Pool(units) as p:
        results_map = p.map(run_method, func_args)
        results = reduce(lambda a, b: a + b if b is not None else a, results_map)

    stop_time = datetime.now()

    if not args.continuous_write:
        with open(filename, 'w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=field_delim, quoting=csv.QUOTE_ALL)
            for r in results:
                write_to_csv(csv_writer, r)

    total = 0
    print("\nReport:")
    print("  Execution time: %s seconds" % (stop_time - start_time))
    print("  Results per engine:")
    for r in results:
        stats_dict[r['engine']] += 1
    for s in stats_dict:
        n = stats_dict[s]
        print("    {}: {}".format(s, str(n)))
        total += n
    print("  Total: {} links written to {}".format(str(total), filename))
