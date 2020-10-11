# OnionSearch
## Educational purposes only
[![forthebadge made-with-python](http://ForTheBadge.com/images/badges/made-with-python.svg)](https://www.python.org/)

OnionSearch is a Python3 script that scrapes urls on different ".onion" search engines.

In 30 minutes you get thousands of unique urls.

## 💡 Prerequisite
[Python 3](https://www.python.org/download/releases/3.0/)

## 📚 Currently supported Search engines
## Modules :
- ahmia
- darksearchio
- onionland
- notevil
- darksearchenginer
- phobos
- onionsearchserver
- torgle x2
- onionsearchengine
- tordex
- tor66
- tormax
- haystack
- multivac
- evosearch
- deeplink

## 🛠️ Installation
### With PyPI

```pip3 install onionsearch```

### With Github

```bash
git clone https://github.com/megadose/OnionSearch.git
cd OnionSearch/
python3 setup.py install
```


## 📈  Usage

Help:
```
usage: onionsearch [-h] [--proxy PROXY] [--output OUTPUT]
                  [--continuous_write CONTINUOUS_WRITE] [--limit LIMIT]
                  [--engines [ENGINES [ENGINES ...]]]
                  [--exclude [EXCLUDE [EXCLUDE ...]]]
                  [--fields [FIELDS [FIELDS ...]]]
                  [--field_delimiter FIELD_DELIMITER] [--mp_units MP_UNITS]
                  search

positional arguments:
  search                The search string or phrase

optional arguments:
  -h, --help            show this help message and exit
  --proxy PROXY         Set Tor proxy (default: 127.0.0.1:9050)
  --output OUTPUT       Output File (default: output_$SEARCH_$DATE.txt), where $SEARCH is replaced by the first chars of the search string and $DATE is replaced by the datetime
  --continuous_write CONTINUOUS_WRITE
                        Write progressively to output file (default: False)
  --limit LIMIT         Set a max number of pages per engine to load
  --engines [ENGINES [ENGINES ...]]
                        Engines to request (default: full list)
  --exclude [EXCLUDE [EXCLUDE ...]]
                        Engines to exclude (default: none)
  --fields [FIELDS [FIELDS ...]]
                        Fields to output to csv file (default: engine name link), available fields are shown below
  --field_delimiter FIELD_DELIMITER
                        Delimiter for the CSV fields
  --mp_units MP_UNITS   Number of processing units (default: core number minus 1)

[...]
```

### Multi-processing behaviour

By default, the script will run with the parameter `mp_units = cpu_count() - 1`. It means if you have a machine with 4 cores,
it will run 3 scraping functions in parallel. You can force `mp_units` to any value but it is recommended to leave to default.
You may want to set it to 1 to run all requests sequentially (disabling multi-processing feature).

Please note that continuous writing to csv file has not been *heavily* tested with multiprocessing feature and therefore
may not work as expected.

Please also note that the progress bars may not be properly displayed when `mp_units` is greater than 1.
**It does not affect the results**, so don't worry.

### Examples

To request all the engines for the word "computer":
```
onionsearch "computer"
```

To request all the engines excepted "Ahmia" and "Candle" for the word "computer":
```
onionsearch "computer" --exclude ahmia candle
```

To request only "Tor66", "DeepLink" and "Phobos" for the word "computer":
```
onionsearch "computer" --engines tor66 deeplink phobos
```

The same as previously but limiting to 3 the number of pages to load per engine:
```
onionsearch "computer" --engines tor66 deeplink phobos --limit 3
```

Please kindly note that the list of supported engines (and their keys) is given in the script help (-h).


### Output

#### Default output

By default, the file is written at the end of the process. The file will be csv formatted, containing the following columns:
```
"engine","name of the link","url"
```

#### Customizing the output fields

You can customize what will be flush in the output file by using the parameters `--fields` and `--field_delimiter`.

`--fields` allows you to add, remove, re-order the output fields. The default mode is show just below. Instead, you can for instance
choose to output:
```
"engine","name of the link","url","domain"
```
by setting `--fields engine name link domain`.

Or even, you can choose to output:
```
"engine","domain"
```
by setting `--fields engine domain`.

These are examples but there are many possibilities.

Finally, you can also choose to modify the CSV delimiter (comma by default), for instance: `--field_delimiter ";"`.

#### Changing filename

The filename will be set by default to `output_$DATE_$SEARCH.txt`, where $DATE represents the current datetime and $SEARCH the first
characters of the search string.

You can modify this filename by using `--output` when running the script, for instance:
```
onionsearch "computer" --output "\$DATE.csv"
onionsearch "computer" --output output.txt
onionsearch "computer" --output "\$DATE_\$SEARCH.csv"
...
```
(Note that it might be necessary to escape the dollar character.)

In the csv file produced, the name and url strings are sanitized as much as possible, but there might still be some problems...

#### Write progressively

You can choose to progressively write to the output (instead of everything at the end, which would prevent
losing the results if something goes wrong). To do so you have to use `--continuous_write True`, just as is:
```
onionsearch "computer" --continuous_write True
```
You can then use the `tail -f` (tail follow) Unix command to actively watch or monitor the results of the scraping.
## Thank you to [Gobarigo](https://github.com/Gobarigo)


## 📝 License
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.fr.html)
