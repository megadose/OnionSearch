import requests,json
from bs4 import BeautifulSoup
import argparse
from tqdm import tqdm
parser = argparse.ArgumentParser()
required = parser.add_argument_group('required arguments')
parser.add_argument("--proxy", default='localhost:9050', type=str, help="Set Tor proxy (default: 127.0.0.1:9050)")
parser.add_argument("--output", default='output.txt', type=str, help="Output File (default: output.txt)")

parser.add_argument("--search",type=str, help="search")
args = parser.parse_args()
proxies = {'http': 'socks5h://{}'.format(args.proxy), 'https': 'socks5h://{}'.format(args.proxy)}

def clear(toclear):
    return(toclear.replace("\n","").replace(" ",""))
def clearn(toclear):
    return(toclear.replace("\n"," "))

def scrape():
    result = {}
    ahmia = "http://msydqstlz2kzerdg.onion/search/?q="+args.search
    response = requests.get(ahmia, proxies=proxies)
    #print(response)
    soup = BeautifulSoup(response.text, 'html.parser')
    result['ahmia'] = []
    #pageNumber = clear(soup.find("span", id="pageResultEnd").get_text())
    for i in tqdm(soup.findAll('li', attrs = {'class' : 'result'}),desc="Ahmia"):
        i = i.find('h4')
        result['ahmia'].append({"name":clear(i.get_text()),"link":i.find('a')['href'].replace("/search/search/redirect?search_term=search&redirect_url=","")})

    urlTorchNumber = "http://xmh57jrzrnw6insl.onion/4a1f6b371c/search.cgi?cmd=Search!&np=1&q="
    req = requests.get(urlTorchNumber+args.search,proxies=proxies)
    soup = BeautifulSoup(req.text, 'html.parser')
    result['urlTorch'] = []
    pageNumber = ""
    for i in soup.find("table",attrs={"width":"100%"}).findAll("small"):
        if("of"in i.get_text()):
            pageNumber = i.get_text()
    pageNumber = round(float(clear(pageNumber.split("-")[1].split("of")[1]))/10)
    if(pageNumber>99):
        pageNumber=99
    result['urlTorch'] = []
    for n in tqdm(range(1,pageNumber+1),desc="Torch"):
        urlTorch = "http://xmh57jrzrnw6insl.onion/4a1f6b371c/search.cgi?cmd=Search!&np={}&q={}".format(n,args.search)
        #print(urlTorch)
        try:
            req = requests.get(urlTorchNumber+args.search,proxies=proxies)
            soup = BeautifulSoup(req.text, 'html.parser')
            for i in soup.findAll('dl'):
                result['urlTorch'].append({"name":clear(i.find('a').get_text()),"link":i.find('a')['href']})
        except:
            pass

    darksearchnumber = "http://darksearch.io/api/search?query="
    req = requests.get(darksearchnumber+args.search,proxies=proxies)
    cookies = req.cookies
    if(req.status_code==200):
        result['darksearch']=[]
        #print(req)
        req = req.json()
        if(req['last_page']>30):
            pageNumber=30
        else:
            pageNumber=req['last_page']
        #print(pageNumber)
        for i in tqdm(range(1,pageNumber+1),desc="Darksearch io"):
            #print(i)
            darksearch = "http://darksearch.io/api/search?query={}&page=".format(args.search)
            req = requests.get(darksearch+str(pageNumber),proxies=proxies,cookies=cookies)
            if(req.status_code==200):
                for r in req.json()['data']:
                    result['darksearch'].append({"name":r["title"],"link":r["link"]})

    else:
        print("Rate limit darksearch.io !")

    result['onionland'] = []
    for n in tqdm(range(1,400),desc="OnionLand"):
        onionland = "http://3bbaaaccczcbdddz.onion/search?q={}&page={}".format(args.search,n)
        #print(urlTorch)
        req = requests.get(onionland,proxies=proxies)
        if(req.status_code==200):
            soup = BeautifulSoup(req.text, 'html.parser')
            for i in soup.findAll('div',attrs={"class":"result-block"}):
                if('''<span class="label-ad">Ad</span>''' not in i):
                    #print({"name":i.find('div',attrs={'class':"title"}).get_text(),"link":clear(i.find('div',attrs={'class':"link"}).get_text())})
                    result['onionland'].append({"name":i.find('div',attrs={'class':"title"}).get_text(),"link":clear(i.find('div',attrs={'class':"link"}).get_text())})
        else:
            break

    print("Ahmia : " + str(len(result['ahmia'])))
    print("Torch : "+str(len(result['urlTorch'])))
    print("Darksearch io : "+str(len(result['darksearch'])))
    print("Onionland : "+str(len(result['onionland'])))
    print("Total of {} links !\nExported to {}".format(str(len(result['ahmia'])+len(result['urlTorch'])+len(result['darksearch'])+len(result['onionland'])),args.output))
    f= open(args.output,"w+")
    for i in result['urlTorch']:
        f.write("name : {} link: {}\n".format(clearn(i["name"]),i["link"]))
    for i in result['onionland']:
        f.write("name: {} link : {}\n".format(clearn(i["name"]),i["link"]))
    for i in result['ahmia']:
        f.write("name : {} link : {}\n".format(clearn(i["name"]),i["link"]))
    for i in result['darksearch']:
        f.write("name : {} link : {}\n".format(clearn(i["name"]),i["link"]))

    f.close()
scrape()
