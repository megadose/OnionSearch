# OnionSearch - Turkish
![PyPI](https://img.shields.io/pypi/v/onionsearch) ![PyPI - Hafta](https://img.shields.io/pypi/dw/onionsearch) ![PyPI - İndir](https://static.pepy.tech/badge/onionsearch) ![PyPI - Lisans](https://img.shields.io/pypi/l/onionsearch)
#### BTC Bağışları İçin : 1FHDM49QfZX6pJmhjLE5tB2K6CaTLMZpXZ
## Yalnızca Eğitim Amaçlı

## !!UYARI!!

OnionSearch, farklı ".onion" arama motorlarındaki URL'leri kazıyan bir Python3 komut dosyasıdır.

![](https://files.catbox.moe/vguy1e.png)

### Demo

![](https://github.com/megadose/gif-demo/raw/master/onionsearch.gif)


## 💡 Önkoşul
[Python 3](https://www.python.org/download/releases/3.0/)

## 📚 Şu anda desteklenen Arama motorları
- ahmia
- darksearchio
- onionland
- notevil
- darksearchenginer
- phobos
- onionsearchserver
- torgle
- onionsearchengine
- tordex
- tor66
- tormax
- haystack
- multivac
- evosearch
- deeplink

## 🛠️ İndirme
### PyPI ile

```pip3 install onionsearch```

### Github ile

```bash
git clone https://github.com/megadose/OnionSearch.git
cd OnionSearch/
python3 setup.py install
```


## 📈  Kullanım
Tabi, işte çevirisi:

```
Yardım:
```
```
kullanım: onionsearch [-h] [--proxy PROXY] [--output OUTPUT]
                  [--continuous_write CONTINUOUS_WRITE] [--limit LIMIT]
                  [--engines [ENGINES [ENGINES ...]]]
                  [--exclude [EXCLUDE [EXCLUDE ...]]]
                  [--fields [FIELDS [FIELDS ...]]]
                  [--field_delimiter FIELD_DELIMITER] [--mp_units MP_UNITS]
                  search

konumsal argümanlar:
  search                Arama dizesi veya ifade

isteğe bağlı argümanlar:
  -h, --help            Bu yardım mesajını göster ve çık
  --proxy PROXY         Tor proxy ayarla (varsayılan: 127.0.0.1:9050)
  --output OUTPUT       Çıkış Dosyası (varsayılan: output_$SEARCH_$DATE.txt), burada $SEARCH arama dizesinin ilk karakterleri ile değiştirilir ve $DATE tarih saat ile değiştirilir
  --continuous_write CONTINUOUS_WRITE
                        Çıktı dosyasına sürekli olarak yaz (varsayılan: False)
  --limit LIMIT         Yüklenecek maksimum sayfa sayısını ayarla
  --engines [ENGINES [ENGINES ...]]
                        İstek gönderilecek motorlar (varsayılan: tam liste)
  --exclude [EXCLUDE [EXCLUDE ...]]
                        Hariç tutulacak motorlar (varsayılan: yok)
  --fields [FIELDS [FIELDS ...]]
                        Csv dosyasına çıktı alınacak alanlar (varsayılan: motor adı link), mevcut alanlar aşağıda gösterilmiştir
  --field_delimiter FIELD_DELIMITER
                        CSV alanları için ayraç
  --mp_units MP_UNITS   İşlem birimi sayısı (varsayılan: çekirdek sayısı eksi 1)

[...]
```

### Çoklu İşlem Davranışı

Varsayılan olarak, betik `mp_units = cpu_count() - 1` parametresiyle çalışacaktır. Yani, 4 çekirdekli bir makineniz varsa,
3 adet veri çekme işlevini paralel olarak çalıştıracaktır. `mp_units`'i istediğiniz bir değere zorlayabilirsiniz, ancak varsayılan değerde bırakmanız önerilir.
Tüm istekleri sırayla çalıştırmak için `mp_units`'i 1 olarak ayarlayabilirsiniz (çoklu işlem özelliğini devre dışı bırakarak).

Lütfen, sürekli olarak csv dosyasına yazma işlemi, çoklu işlem özelliği ile *yoğun bir şekilde* test edilmemiş olabilir ve bu nedenle
beklendiği gibi çalışmayabilir.

Lütfen ayrıca, `mp_units` 1'den büyük olduğunda ilerleme çubuklarının düzgün bir şekilde gösterilmeyebileceğini unutmayın.
**Bu sonuçları etkilemez**, endişelenmeyin.

### Örnekler

"computer" kelimesi için tüm motorlardan istekte bulunmak için:
```
onionsearch "computer"
```

"computer" kelimesi için "Ahmia" ve "Candle" hariç tüm motorlardan istekte bulunmak için:
```
onionsearch "computer" --exclude ahmia candle
```

Sadece "Tor66", "DeepLink" ve "Phobos" için "computer" kelimesinden istekte bulunmak için:
```
onionsearch "computer" --engines tor66 deeplink phobos
```

Öncekinden aynı ancak her motor için yüklenecek sayfa sayısını 3'e sınırlamak için:
```
onionsearch "computer" --engines tor66 deeplink phobos --limit 3
```

Lütfen desteklenen motorların (ve anahtarlarının) listesi betik yardımında (-h) verilmiştir.


### Çıktı

#### Varsayılan çıktı

Varsayılan olarak, dosya işlem sonunda yazılır. Dosya csv formatında olacak ve aşağıdaki sütunları içerecektir:
```
"motor","bağlantı adı","url"
```

#### Çıktı alanlarını özelleştirme

Çıktı dosyasına neyin yazılacağını `--fields` ve `--field_delimiter` parametrelerini kullanarak özelleştirebilirsiniz.

`--fields`, çıktı alanlarına eklemek, çıkarmak, yeniden düzenlemek için kullanılır. Varsayılan mod aşağıda gösterilmiştir. Bunun yerine örneğin
şunu çıktı almak için:
```
"motor","bağlantı adı","url","alan"
```
`--fields` parametresini `engine name link domain` olarak ayarlayarak yapabilirsiniz.

Ya da hatta şunu çıktı almak için:
```
"motor","alan"
```
`--fields` parametresini `engine domain` olarak ayarlayarak yapabilirsiniz.

Bunlar örneklerdir ancak birçok olasılık vardır.

Son olarak, CSV ayraçını (varsayılan olarak virgül) değiştirmeyi seçebilirsiniz, örneğin: `--field_delimiter ";"`.

#### Dosya adını değiştirme

Dosya adı varsayılan olarak `output_$DATE_$SEARCH.txt` olarak ayarlanacaktır, burada $DATE geçerli tarih ve saatı, $SEARCH ise arama dizesinin ilk karakterlerini temsil eder.

Betik çalıştırılırken bunu `--output` kullanarak değiştirebilirsiniz, örneğin:
```
onionsearch "computer" --output "\$DATE.csv"
onionsearch "computer" --output output.txt
onionsearch "computer" --output "\$DATE_\$SEARCH.csv"
...
```
(Nota: Dolar işareti karakterini kaçırmak gerekebilir.)

Üretilen csv dosyasında, ad ve url dizeleri mümkün olduğunca temizlenmiş olsa da, hala bazı sorunlar olabilir...
#### Write progressively

Çıktıya aşamalı olarak yazmayı seçebilirsiniz (sondaki her şey yerine, bu da bir şeyler ters giderse sonuçları kaybetmek). Bunu yapmak için kullanmanız gerekir `--continuous_write True`, Aynen olduğu gibi:
```
onionsearch "computer" --continuous_write True
```
Daha sonra, kazıma sonuçlarını aktif olarak izlemek veya izlemek için 'tail -f' (kuyruk takibi) Unix komutunu kullanabilirsiniz. 

## [Gobarigo]'ya teşekkürler(https://github.com/Gobarigo) 
## Bu logo için teşekkür ederim [mxrch](https://github.com/mxrch)

## [01Kevin01](https://github.com/01Kevin01)
* Ek onion link kaynakları için https://github.com/01Kevin01/OnionLinksV3
* 📄 [OnionLinksV3.md](https://github.com/01Kevin01/OnionLinksV3/blob/main/OnionLinksV3.md)
* My e-mail:01Kevin0110@proton.me

## 📝 License
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.fr.html)
