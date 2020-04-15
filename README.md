# OnionSearch
## Educational purposes only
[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

OnionSearch is a Python3 script that scrapes urls on different ".onion" search engines. 

In 30 minutes you get thousands of unique urls.

## 💡 Prerequisite
[Python 3](https://www.python.org/download/releases/3.0/)
   
## 📚 Currently supported Search engines
- Ahmia
- TORCH
- Darksearch io
- OnionLand
- not Evil
- VisiTOR
- Dark Search Enginer
- Phobos
- Onion Search Server
- Grams
- Candle
- Tor Search Engine
- Torgle
- Onion Search Engine
- Tordex
- Tor66
- Tormax
- Haystack
- Multivac
- Evo Search
- Oneirun
- DeepLink

## 🛠️ Installation

```
git clone https://github.com/megadose/OnionSearch.git
cd OnionSearch
pip3 install -r requirements.txt
pip3 install 'urllib3[socks]'
python3 search.py -h
```

## 📈  Usage

```
usage: search.py [-h] [--proxy PROXY] [--output OUTPUT] [--limit LIMIT]
                 [--barmode BARMODE] [--engines [ENGINES [ENGINES ...]]]
                 [--exclude [EXCLUDE [EXCLUDE ...]]]
                 search

positional arguments:
  search                The search string or phrase

optional arguments:
  -h, --help            show this help message and exit
  --proxy PROXY         Set Tor proxy (default: 127.0.0.1:9050)
  --output OUTPUT       Output File (default: output_$SEARCH_$DATE.txt), where
                        $SEARCH is replaced by the first chars of the search
                        string and $DATE is replaced by the datetime
  --limit LIMIT         Set a max number of pages per engine to load
  --barmode BARMODE     Can be 'fixed' (default) or 'unknown'
  --engines [ENGINES [ENGINES ...]]
                        Engines to request (default: full list)
  --exclude [EXCLUDE [EXCLUDE ...]]
                        Engines to exclude (default: none)

[...]
```

### Examples

To request all the engines for the word "computer":
```
python3 search.py "computer"
```

To request all the engines excepted "Ahmia" and "Candle" for the word "computer":
```
python3 search.py "computer" --exclude ahmia candle
```

To request only "Tor66", "DeepLink" and "Phobos" for the word "computer":
```
python3 search.py "computer" --engines tor66 deeplink phobos
```

The same as previously but limiting to 3 the number of pages to load per engine:
```
python3 search.py "computer" --engines tor66 deeplink phobos --limit 3
```

Please kindly note that the list of supported engines (and their keys) is given in the script help (-h).


### Output

The file written at the end of the process will be a csv containing the following columns:
```
"engine","name of the link","url"
```

The filename will be set by default to `output_$DATE_$SEARCH.txt`, where $DATE represents the current datetime and $SEARCH the first
characters of the search string.

You can modify this filename by using `--output` when running the script, for instance:
```
python3 search.py "computer" --output "\$DATE.csv"
python3 search.py "computer" --output output.txt
python3 search.py "computer" --output "\$DATE_\$SEARCH.csv"
...
```
(Note that it might be necessary to escape the dollar character.)

In the csv file produced, the name and url strings are sanitized as much as possible, but there might still be some problems.


## 📝 License
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.fr.html)


