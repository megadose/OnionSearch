#!/usr/bin/python3
import constants

import argparse
import csv
import math
import re
import time
import urllib.parse as urlparse
from datetime import datetime
from functools import reduce
from multiprocessing import Pool, cpu_count, current_process, freeze_support
from random import choice
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

supported_engines = constants.ENGINES


def print_epilog():
    epilog = "Available CSV fields: \n\t"
    for f in constants.available_csv_fields:
        epilog += f" {f}"
    epilog += "\n"
    epilog += "Supported engines: \n\t"
    for e in supported_engines.keys():
        epilog += f" {e}"
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
proxies = {
    'http': f'socks5h://{args.proxy}',
    'https': f'socks5h://{args.proxy}',
}
filename = args.output
field_delim = ","
if args.field_delimiter and len(args.field_delimiter) == 1:
    field_delim = args.field_delimiter


def random_headers():
    """
        Generate a dictionary containing HTTP headers with a random 'User-Agent' and a standard 'Accept' header.

        The 'User-Agent' header is chosen randomly from a predefined list of user agents for desktop browsers,
        which is expected to be defined in a separate module named 'constants' under the attribute 'desktop_agents'.

        Returns:
            dict: A dictionary with the following structure:
                  {
                      'User-Agent': A random user agent string from 'constants.desktop_agents',
                      'Accept': A standard accept header string for HTTP requests
                  }

        Example:
            >>> random_headers()
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
        """
    return {'User-Agent': choice(constants.desktop_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}


def clear(toclear) -> str:
    """
        Cleans up a string by replacing newline characters with spaces and
        collapsing multiple whitespace characters into a single space.

        Parameters:
            toclear (str): The string to be cleaned.

        Returns:
            str: The cleaned string with newline characters replaced by spaces
                 and consecutive whitespace collapsed into single spaces.

        Example:
            >>> sample_text = "This is a text\\nwith newlines\\n\\n    and irregular spacing."
            >>> clear(sample_text)
            'This is a text with newlines and irregular spacing.'
        """
    str_cleaned = toclear.replace("\n", " ")
    str_cleaned = ' '.join(str_cleaned.split())
    return str_cleaned


def get_parameter(url, parameter_name):
    """
        Extract the value of a given parameter from the query string of a URL.

        Parameters:
            url (str): The URL containing the query string.
            parameter_name (str): The name of the parameter to retrieve the value for.

        Returns:
            str: The value of the requested parameter.

        Raises:
            IndexError: If the parameter is not found in the query string, or if it has no values.

        Example:
            >>> get_parameter("http://example.com?param1=value1&param2=value2", 'param1')
            'value1'
            >>> get_parameter("http://example.com?param1=value1&param2=value2", 'param2')
            'value2'

        Note:
            The function assumes that the 'urlparse' and 'parse_qs' methods are available from the 'urllib.parse' module,
            and they need to be imported before calling this function:

            from urllib.parse import urlparse, parse_qs
        """
    parsed = urlparse.urlparse(url)
    return parse_qs(parsed.query)[parameter_name][0]


def get_proc_pos():
    """
        Retrieves the zero-based position index of the current process.

        This function assumes that it is being called within a process of a multiprocessing context.
        It fetches the unique identity of the current process and adjusts it to get a zero-based index
        by subtracting 1, as the identity is 1-based by default.

        Returns:
            int: The zero-based index position of the current process.

        Example:
            # Assuming this function is called within a Process of a multiprocessing Pool
            >>> from multiprocessing import current_process
            >>> get_proc_pos()
            0   # If it's the first process created in the pool

        Note:
            The function uses 'current_process' from the 'multiprocessing' module, which needs to be
            imported before calling this function:

            from multiprocessing import current_process
        """
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


def darksearchio(searchstr):
    results = []
    darksearchio_url = supported_engines['darksearchio'] + "/api/search?query={}&page={}"
    max_nb_page = args.limit if args.limit != 0 else 30
    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()
        resp = s.get(darksearchio_url.format(quote(searchstr), 1))

        if resp.status_code != 200:
            return

        resp = resp.json()
        page_number = resp['last_page'] if 'last_page' in resp else 1
        page_number = min(page_number, max_nb_page)
        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("DarkSearch (.io)", pos), position=pos) \
                as progress_bar:

            results = link_finder("darksearchio", resp['data'])
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(darksearchio_url.format(quote(searchstr), n))
                if resp.status_code == 200:
                    resp = resp.json()
                    results = results + link_finder("darksearchio", resp['data'])
                    progress_bar.update()
                else:
                    # Current page results will be lost but we will try to continue after a short sleep
                    time.sleep(1)

    return results


def onionland(searchstr):
    results = []
    onionlandv3_url = supported_engines['onionland'] + "/search?q={}&page={}"
    max_nb_page = args.limit if args.limit != 0 else 100
    with requests.Session() as s:
        results = _extracted_from_onionland_9(
            s, onionlandv3_url, searchstr, max_nb_page
        )
    return results


# TODO Rename this here and in `onionland`
def _extracted_from_onionland_9(s, onionlandv3_url, searchstr, max_nb_page):
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
            page_number = math.ceil(nb_res / 19)
            page_number = min(page_number, max_nb_page)
    pos = get_proc_pos()
    with tqdm(total=max_nb_page, initial=0, desc=get_tqdm_desc("OnionLand", pos), position=pos) as progress_bar:

        result = link_finder("onionland", soup)
        progress_bar.update()

        for n in range(2, page_number + 1):
            resp = s.get(onionlandv3_url.format(quote(searchstr), n))
            soup = BeautifulSoup(resp.text, 'html5lib')
            ret = link_finder("onionland", soup)
            if len(ret) == 0:
                break
            result = result + ret
            progress_bar.update()

    return result


def notevil(searchstr):
    results = []
    notevil_url1 = supported_engines['notevil'] + "/index.php?q={}"
    notevil_url2 = supported_engines['notevil'] + "/index.php?q={}&hostLimit=20&start={}&numRows={}&template=0"
    max_nb_page = args.limit if args.limit != 0 else 20
    # Do not use requests.Session() here (by experience less results would be got)
    req = requests.get(notevil_url1.format(quote(searchstr)), proxies=proxies, headers=random_headers())
    soup = BeautifulSoup(req.text, 'html5lib')

    page_number = 1
    last_div = soup.find("div", attrs={"style": "text-align:center"}).find("div", attrs={"style": "text-align:center"})
    if last_div is not None:
        for i in last_div.find_all("a"):
            page_number = int(i.get_text())
        page_number = min(page_number, max_nb_page)
    pos = get_proc_pos()
    with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("not Evil", pos), position=pos) as progress_bar:
        num_rows = 20
        results = link_finder("notevil", soup)
        progress_bar.update()

        for n in range(2, page_number + 1):
            start = (int(n - 1) * num_rows)
            req = requests.get(notevil_url2.format(quote(searchstr), start, num_rows),
                               proxies=proxies,
                               headers=random_headers())
            soup = BeautifulSoup(req.text, 'html5lib')
            results = results + link_finder("notevil", soup)
            progress_bar.update()
            time.sleep(1)

    return results


def darksearchenginer(searchstr):
    results = []
    darksearchenginer_url = supported_engines['darksearchenginer']
    max_nb_page = args.limit if args.limit != 0 else 20
    page_number = 1

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        # Note that this search engine is very likely to timeout
        resp = s.post(darksearchenginer_url, data={"search[keyword]": searchstr, "page": page_number})
        soup = BeautifulSoup(resp.text, 'html5lib')

        pages_input = soup.find_all("input", attrs={"name": "page"})
        for i in pages_input:
            page_number = int(i['value'])
            page_number = min(page_number, max_nb_page)
        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Dark Search Enginer", pos), position=pos) \
                as progress_bar:

            results = link_finder("darksearchenginer", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.post(darksearchenginer_url, data={"search[keyword]": searchstr, "page": str(n)})
                soup = BeautifulSoup(resp.text, 'html5lib')
                results = results + link_finder("darksearchenginer", soup)
                progress_bar.update()

    return results


def phobos(searchstr):
    results = []
    phobos_url = supported_engines['phobos'] + "/search?query={}&p={}"
    max_nb_page = args.limit if args.limit != 0 else 100
    with requests.Session() as s:
        results = _extracted_from_phobos_(s, phobos_url, searchstr, max_nb_page)
    return results


# TODO Rename this here and in `phobos`
def _extracted_from_phobos_(s, phobos_url, searchstr, max_nb_page):
    s.proxies = proxies
    s.headers = random_headers()

    resp = s.get(phobos_url.format(quote(searchstr), 1), proxies=proxies, headers=random_headers())
    soup = BeautifulSoup(resp.text, 'html5lib')

    page_number = 1
    pages = soup.find("div", attrs={"class": "pages"}).find_all('a')
    if pages is not None:
        for i in pages:
            page_number = int(i.get_text())
        page_number = min(page_number, max_nb_page)
    pos = get_proc_pos()
    with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Phobos", pos), position=pos) as progress_bar:
        result = link_finder("phobos", soup)
        progress_bar.update()

        for n in range(2, page_number + 1):
            resp = s.get(phobos_url.format(quote(searchstr), n), proxies=proxies, headers=random_headers())
            soup = BeautifulSoup(resp.text, 'html5lib')
            result = result + link_finder("phobos", soup)
            progress_bar.update()

    return result


def onionsearchserver(searchstr):
    results = []
    onionsearchserver_url1 = supported_engines['onionsearchserver'] + "/oss/"
    onionsearchserver_url2 = None
    results_per_page = 10
    max_nb_page = args.limit if args.limit != 0 else 100
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
            page_number = min(page_number, max_nb_page)
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


def onionsearchengine(searchstr):
    results = []
    onionsearchengine_url = supported_engines['onionsearchengine'] + "/search.php?search={}&submit=Search&page={}"
    max_nb_page = args.limit if args.limit != 0 else 100
    with requests.Session() as s:
        results = _extracted_from_onionsearchengine_10(
            s, onionsearchengine_url, searchstr, max_nb_page
        )
    return results


# TODO Rename this here and in `onionsearchengine`
def _extracted_from_onionsearchengine_10(s, onionsearchengine_url, searchstr, max_nb_page):
    s.proxies = proxies
    s.headers = random_headers()

    resp = s.get(onionsearchengine_url.format(quote(searchstr), 1))
    soup = BeautifulSoup(resp.text, 'html5lib')

    page_number = 1
    approx_re = re.search(r"\s([0-9]+)\sresult[s]?\sfound\s!.*", clear(soup.find('body').get_text()))
    if approx_re is not None:
        nb_res = int(approx_re[1])
        page_number = math.ceil(float(nb_res / 9))
        page_number = min(page_number, max_nb_page)
    pos = get_proc_pos()
    with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Onion Search Engine", pos), position=pos) \
            as progress_bar:

        result = link_finder("onionsearchengine", soup)
        progress_bar.update()

        for n in range(2, page_number + 1):
            resp = s.get(onionsearchengine_url.format(quote(searchstr), n))
            soup = BeautifulSoup(resp.text, 'html5lib')
            result = result + link_finder("onionsearchengine", soup)
            progress_bar.update()

    return result


def tordex(searchstr):
    results = []
    tordex_url = supported_engines['tordex'] + "/search?query={}&page={}"
    max_nb_page = args.limit if args.limit != 0 else 100
    with requests.Session() as s:
        results = _extracted_from_tordex_(s, tordex_url, searchstr, max_nb_page)
    return results


# TODO Rename this here and in `tordex`
def _extracted_from_tordex_(s, tordex_url, searchstr, max_nb_page):
    s.proxies = proxies
    s.headers = random_headers()

    resp = s.get(tordex_url.format(quote(searchstr), 1))
    soup = BeautifulSoup(resp.text, 'html5lib')

    page_number = 1
    pages = soup.find_all("li", attrs={"class": "page-item"})
    if pages is not None:
        for i in pages:
            if i.get_text() != "...":
                page_number = int(i.get_text())
        page_number = min(page_number, max_nb_page)
    pos = get_proc_pos()
    with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Tordex", pos), position=pos) as progress_bar:

        result = link_finder("tordex", soup)
        progress_bar.update()

        for n in range(2, page_number + 1):
            resp = s.get(tordex_url.format(quote(searchstr), n))
            soup = BeautifulSoup(resp.text, 'html5lib')
            result = result + link_finder("tordex", soup)
            progress_bar.update()

    return result


def tor66(searchstr):
    results = []
    tor66_url = supported_engines['tor66'] + "/search?q={}&sorttype=rel&page={}"
    max_nb_page = args.limit if args.limit != 0 else 30
    with requests.Session() as s:
        results = _extracted_from_tor66_9(s, tor66_url, searchstr, max_nb_page)
    return results


# TODO Rename this here and in `tor66`
def _extracted_from_tor66_9(s, tor66_url, searchstr, max_nb_page):
    s.proxies = proxies
    s.headers = random_headers()

    resp = s.get(tor66_url.format(quote(searchstr), 1))
    soup = BeautifulSoup(resp.text, 'html5lib')

    page_number = 1
    approx_re = re.search(r"\.Onion\ssites\sfound\s:\s([0-9]+)", resp.text)
    if approx_re is not None:
        nb_res = int(approx_re.group(1))
        page_number = math.ceil(float(nb_res / 20))
        page_number = min(page_number, max_nb_page)
    pos = get_proc_pos()
    with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Tor66", pos), position=pos) as progress_bar:

        result = link_finder("tor66", soup)
        progress_bar.update()

        for n in range(2, page_number + 1):
            resp = s.get(tor66_url.format(quote(searchstr), n))
            soup = BeautifulSoup(resp.text, 'html5lib')
            result = result + link_finder("tor66", soup)
            progress_bar.update()

    return result


def tormax(searchstr):
    results = []
    tormax_url = supported_engines['tormax'] + "/search?q={}"

    pos = get_proc_pos()
    with tqdm(total=1, initial=0, desc=get_tqdm_desc("Tormax", pos), position=pos) as progress_bar:
        response = requests.get(tormax_url.format(quote(searchstr)), proxies=proxies, headers=random_headers())
        soup = BeautifulSoup(response.text, 'html5lib')
        results = link_finder("tormax", soup)
        progress_bar.update()

    return results


def haystack(searchstr):
    results = []
    haystack_url = supported_engines['haystack'] + "/?q={}&offset={}"
    max_nb_page = args.limit if args.limit != 0 else 50
    offset_coeff = 20

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        req = s.get(haystack_url.format(quote(searchstr), 0))
        soup = BeautifulSoup(req.text, 'html5lib')

        pos = get_proc_pos()
        with tqdm(total=max_nb_page, initial=0, desc=get_tqdm_desc("Haystack", pos), position=pos) as progress_bar:
            ret = link_finder("haystack", soup)
            results += ret
            progress_bar.update()
            continue_processing = len(ret) != 0
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


def multivac(searchstr):
    results = []
    multivac_url = supported_engines['multivac'] + "/?q={}&page={}"
    max_nb_page = args.limit if args.limit != 0 else 10
    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        page_to_request = 1
        req = s.get(multivac_url.format(quote(searchstr), page_to_request))
        soup = BeautifulSoup(req.text, 'html5lib')

        pos = get_proc_pos()
        with tqdm(total=max_nb_page, initial=0, desc=get_tqdm_desc("Multivac", pos), position=pos) as progress_bar:
            ret = link_finder("multivac", soup)
            results += ret
            progress_bar.update()
            continue_processing = len(ret) != 0 and page_to_request < max_nb_page
            while continue_processing:
                page_to_request += 1
                req = s.get(multivac_url.format(quote(searchstr), page_to_request))
                soup = BeautifulSoup(req.text, 'html5lib')
                ret = link_finder("multivac", soup)
                results = results + ret
                progress_bar.update()
                if len(ret) == 0 or page_to_request >= max_nb_page:
                    continue_processing = False

    return results


def evosearch(searchstr):
    results = []
    evosearch_url = supported_engines['evosearch'] + "/evo/search.php?" \
                                                     "query={}&" \
                                                     "start={}&" \
                                                     "search=1&type=and&mark=bold+text&" \
                                                     "results={}"
    results_per_page = 50
    max_nb_page = args.limit if args.limit != 0 else 30
    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        req = s.get(evosearch_url.format(quote(searchstr), 1, results_per_page))
        soup = BeautifulSoup(req.text, 'html5lib')

        page_number = 1
        i = soup.find("p", attrs={"class": "cntr"})
        if i is not None and (i.get_text() is not None and "of" in i.get_text()):
            nb_res = float(clear(str.split(i.get_text().split("-")[1].split("of")[1])[0]))
            page_number = math.ceil(nb_res / results_per_page)
            page_number = min(page_number, max_nb_page)
        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Evo Search", pos), position=pos) as progress_bar:
            results = link_finder("evosearch", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                resp = s.get(evosearch_url.format(quote(searchstr), n, results_per_page))
                soup = BeautifulSoup(resp.text, 'html5lib')
                results = results + link_finder("evosearch", soup)
                progress_bar.update()

    return results


def deeplink(searchstr):
    results = []
    deeplink_url1 = supported_engines['deeplink'] + "/index.php"
    deeplink_url2 = supported_engines['deeplink'] + "/?search={}&type=verified"

    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()
        s.get(deeplink_url1)

        pos = get_proc_pos()
        with tqdm(total=1, initial=0, desc=get_tqdm_desc("DeepLink", pos), position=pos) as progress_bar:
            response = s.get(deeplink_url2.format(quote(searchstr)))
            soup = BeautifulSoup(response.text, 'html5lib')
            results = link_finder("deeplink", soup)
            progress_bar.update()

    return results


def torgle1(searchstr):
    results = []
    torgle1_url = supported_engines['torgle1'] + "/torgle/index-frame.php?query={}&search=1&engine-ver=2&isframe=0{}"
    results_per_page = 10
    max_nb_page = args.limit if args.limit != 0 else 30
    with requests.Session() as s:
        s.proxies = proxies
        s.headers = random_headers()

        resp = s.get(torgle1_url.format(quote(searchstr), ""))
        soup = BeautifulSoup(resp.text, 'html5lib')

        page_number = 1
        i = soup.find('div', attrs={"id": "result_report"})
        if i is not None and (i.get_text() is not None and "of" in i.get_text()):
            res_re = re.match(r".*of\s([0-9]+)\s.*", clear(i.get_text()))
            total_results = int(res_re[1])
            page_number = math.ceil(total_results / results_per_page)
            page_number = min(page_number, max_nb_page)
        pos = get_proc_pos()
        with tqdm(total=page_number, initial=0, desc=get_tqdm_desc("Torgle 1", pos), position=pos) as progress_bar:
            results = link_finder("torgle1", soup)
            progress_bar.update()

            for n in range(2, page_number + 1):
                start_page_param = f"&start={n}"
                resp = s.get(torgle1_url.format(quote(searchstr), start_page_param))
                soup = BeautifulSoup(resp.text, 'html5lib')
                results = results + link_finder("torgle1", soup)
                progress_bar.update()

    return results


def get_domain_from_url(link):
    fqdn_re = r"^[a-z][a-z0-9+\-.]*://([a-z0-9\-._~%!$&'()*+,;=]+@)?([a-z0-9\-._~%]+|\[[a-z0-9\-._~%!$&'()*+,;=:]+\])"
    domain_re = re.match(fqdn_re, link)
    if domain_re is not None and domain_re.lastindex == 2:
        return domain_re[2]
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
    else:
        line_to_write.extend((fields['engine'], fields['name'], fields['link']))

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

    if engine_str == "darksearchenginer":
        for r in data_obj.select('.table-responsive a'):
            name = clear(r.get_text())
            link = clear(r['href'])
            add_link()

    if engine_str == "darksearchio":
        for r in data_obj:
            name = clear(r["title"])
            link = clear(r["link"])
            add_link()

    if engine_str == "deeplink":
        for tr in data_obj.find_all('tr'):
            cels = tr.find_all('td')
            if cels is not None and len(cels) == 4:
                name = clear(cels[1].get_text())
                link = clear(cels[0].find('a')['href'])
                add_link()

    if engine_str == "evosearch":
        for r in data_obj.select("#results .title a"):
            name = clear(r.get_text())
            link = get_parameter(r['href'], 'url')
            add_link()

    if engine_str == "haystack":
        for r in data_obj.select(".result b a"):
            name = clear(r.get_text())
            link = get_parameter(r['href'], 'url')
            add_link()

    if engine_str == "multivac":
        for r in data_obj.select("dl dt a"):
            if r['href'] != "":
                name = clear(r.get_text())
                link = clear(r['href'])
                add_link()
            else:
                break

    if engine_str == "notevil":
        for r in data_obj.find_all("p"):
            r = r.find("a")
            name = clear(r.get_text())
            link = unquote(r["href"]).split('./r2d.php?url=')[1].split('&')[0]
            add_link()

    if engine_str == "onionland":
        for r in data_obj.select('.result-block .title a'):
            if not r['href'].startswith('/ads/'):
                name = clear(r.get_text())
                link = unquote(unquote(get_parameter(r['href'], 'l')))
                add_link()

    if engine_str == "onionsearchengine":
        for r in data_obj.select("table a b"):
            name = clear(r.get_text())
            link = get_parameter(r.parent['href'], 'u')
            add_link()

    if engine_str == "onionsearchserver":
        for r in data_obj.select('.osscmnrdr.ossfieldrdr1 a'):
            name = clear(r.get_text())
            link = clear(r['href'])
            add_link()

    if engine_str == "phobos":
        for r in data_obj.select('.serp .titles'):
            name = clear(r.get_text())
            link = clear(r['href'])
            add_link()

    if engine_str == "tor66":
        for i in data_obj.find('hr').find_all_next('b'):
            if i.find('a'):
                name = clear(i.find('a').get_text())
                link = clear(i.find('a')['href'])
                add_link()

    if engine_str == "tordex":
        for r in data_obj.select('.container h5 a'):
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

    if engine_str == "torgle1":
        for r in data_obj.select("#results a.title"):
            name = clear(r.get_text())
            link = clear(r['href'])
            add_link()

    if engine_str == "tormax":
        for r in data_obj.find_all("section", attrs={"id": "search-results"})[0].find_all("article"):
            name = clear(r.find('a', attrs={"class": "title"}).get_text())
            link = clear(r.find('div', attrs={"class": "url"}).get_text())
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
        search = search[:9]
    filename = filename.replace("$SEARCH", search)

    func_args = []
    stats_dict = {}
    if args.engines and len(args.engines) > 0:
        eng = args.engines[0]
        for e in eng:
            try:
                if not (args.exclude and len(args.exclude) > 0 and e in args.exclude[0]):
                    func_args.append(f"{e}:{args.search}")
                    stats_dict[e] = 0
            except KeyError:
                print(f"Error: search engine {e} not in the list of supported engines")
    else:
        for e in supported_engines.keys():
            if not (args.exclude and len(args.exclude) > 0 and e in args.exclude[0]):
                func_args.append(f"{e}:{args.search}")
                stats_dict[e] = 0

    # Doing multiprocessing
    if args.mp_units and args.mp_units > 0:
        units = args.mp_units
    else:
        # Use (cores count - 1), but not less then one, threads
        units = max((cpu_count() - 1), 1)
    print(f"search.py started with {units} processing units...")
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
    print(f"  Execution time: {stop_time - start_time} seconds")
    print("  Results per engine:")
    for r in results:
        stats_dict[r['engine']] += 1
    for s, n in stats_dict.items():
        print(f"    {s}: {str(n)}")
        total += n
    print(f"  Total: {str(total)} links written to {filename}")
