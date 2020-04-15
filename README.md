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
  --output OUTPUT       Output File (default: output.txt)
  --limit LIMIT         Set a max number of pages per engine to load
  --barmode BARMODE     Can be 'fixed' (default) or 'unknown'
  --engines [ENGINES [ENGINES ...]]
                        Engines to request (default: full list)
  --exclude [EXCLUDE [EXCLUDE ...]]
                        Engines to exclude (default: none)
```

### Examples

To request the string "computer" on all the engines to default file:
```
python3 search.py "computer"
```

To request all the engines but "Ahmia" and "Candle":
```
python3 search.py "computer" --proxy 127.0.0.1:1337 --exclude ahmia candle
```

To request only "Tor66", "DeepLink" and "Phobos":
```
python3 search.py "computer" --proxy 127.0.0.1:1337 --engines tor66 deeplink phobos
```

The same but limiting the number of page per engine to load to 3:
```
python3 search.py "computer" --proxy 127.0.0.1:1337 --engines tor66 deeplink phobos --limit 3
```

Please kindly note that the list of supported engines (and their keys) is given in the script help (-h).

### Output

The file written at the end of the process will be a csv containing the following columns:
```
"engine","name of the link","url"
```

The name and url strings are sanitized as much as possible, but there might still be some problems. 


## 📝 License
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.fr.html)


