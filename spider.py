#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 17-4-21 下午10:37
# @Author  : Sylor
# @File    : basic_spider.py
# @Software: PyCharm
from urllib.parse import urlencode
import requests
from lxml.etree import XMLSyntaxError
from requests.exceptions import ConnectionError
from pyquery import PyQuery as pq
import pymongo
from config import *


client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

base_url = 'http://weixin.sogou.com/weixin?'

headers = {
    'Cookie':'IPLOC=JP; SUID=9161BB6A7C20940A0000000058FA15A0; SUV=1492784545630706; ABTEST=7|1492784554|v1; PHPSESSID=74i45b9gpmk8e3oseqfebdlg62; SUIR=1492784554; SNUID=43B069BBD2D49F7F2F2DAFCDD2C0AB65; weixinIndexVisited=1; JSESSIONID=aaaiGWlLfYfq7ascPtFSv; ppinf=5|1492784782|1493994382|dHJ1c3Q6MToxfGNsaWVudGlkOjQ6MjAxN3x1bmlxbmFtZToxMTpIJUUzJTgwJTgxc3xjcnQ6MTA6MTQ5Mjc4NDc4MnxyZWZuaWNrOjExOkglRTMlODAlODFzfHVzZXJpZDo0NDpvOXQybHVQaG8tSVZsS28waThJLVZMaDA0X0Q0QHdlaXhpbi5zb2h1LmNvbXw; pprdig=qotJkZQQKjvxxxRHhA2-jqs5iFUCi0VmcXf-IvuaGOLH4ZTeTDDOB4U4otghjlEubLtCfGVhcfbY5GRBaLB_YDLe4kP5FcoZqGqTEd6m8IMkzkNCXO5dYl0vyEzutrtDS2udS2ZNISCXQLqKtKmRY7IBK4DNOCsc6DdvaqE5ZRg; sgid=; ppmdig=1492784783000000acfb89bb689f7a57a02d137e825be881; sct=4',
    'Host':'weixin.sogou.com',
    'Upgrade-Insecure-Requests':'1',
    'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36'

}
proxy = None

def get_proxy():
    try:
        response = requests.get(PROXY_POOL_URL)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None


def get_html(url,count=1):
    print('Crawling',url)
    print('Trying Count',count)
    global proxy
    if count >= MAX_COUNT:
        print('Tried Too Many Counts')
        return None
    try:
        if proxy:
            proxies = {
                'http':'http://' + proxy
            }
            response = requests.get(url,allow_redirects=False,headers = headers,proxies=proxies)
        else:
            response = requests.get(url,allow_redirects=False,headers = headers)
        if response.status_code == 200:
            return response.text
        if response.status_code ==302:
            print('302')
            proxy = get_proxy()
            if proxy:
                print('Using Proxy',proxy)
                return get_html(url)
            else:
                print('Get Proxy Failed')
                return None
    except ConnectionError as e:
        print('Error Occurred',e.args)


        proxy = get_proxy()
        count += 1
        return get_html(url,count)

def get_index(keyword,page):
    data = {
        'query':keyword,
        'type': 2,
        'page': page
    }
    queries = urlencode(data)
    url = base_url + queries
    html = get_html(url)
    return html

def parse_index(html):
    doc = pq(html)
    items = doc('.news-box .news-list li .txt-box h3 a').items()
    for item in items:
        yield item.attr('href')

def get_detail(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        return None
    except ConnectionError:
        return None

def parse_detail(html):
    try:
        doc = pq(html)
        title = doc('.rich_media_title').text()
        content = doc('.rich_media_content').text()
        date = doc('#post-date').text()
        nickname = doc('#js_profile_qrcode > div > strong').text()
        wechat = doc('#js_profile_qrcode > div > p:nth-child(3) > span').text()
        return {
            'title':title,
            'content':content,
            'date':date,
            'nickname':nickname,
            'wechat':wechat
        }
    except XMLSyntaxError:
        return None

def save_to_mongo(data):
    if db['articles'].update({'title':data['title']},{'$set':data},True):
        print('Save to Mongo',data['title'])
    else:
        print('Save To Mongo Failed',data['title'])




def main():
    for page in range(1,101):
        html = get_index(KEYWORD,page)
        if html:
            article_urls = parse_index(html)
            for  article_url in article_urls:
                article_html = get_detail(article_url)
                if article_html:
                    article_data = parse_detail(article_html)
                    print(article_data)
                    if article_data:
                        save_to_mongo(article_data)




if __name__ == '__main__':
    main()

