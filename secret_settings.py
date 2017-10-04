# -*- coding: utf-8 -*-
"""
Created on Tue Aug 22 14:40:42 2017

Proxy switching and fake user settings
@author: stephen
"""
#set rate of requests to prevent sending too many at once.
download_delay = 5

autothrottle_enabled = True
autothrottle_target_concurrency = 0.5
autothrottle_debug = True
RANDOM_UA_PER_PROXY = True
# Retry many times since proxies often fail
RETRY_TIMES = 10
# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]
DOWNLOADER_MIDDLEWARES = {
       'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
       'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
       'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
       'scrapy_proxies.RandomProxy': 100,
       'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        }
PROXY_LIST = '/home/stephen/Code/Python/venv/SEC/full_proxy.txt'
# Proxy mode
# 0 = Every requests have different proxy
# 1 = Take only one proxy from the list and assign it to every requests
# 2 = Put a custom proxy to use in the settings
PROXY_MODE = 0

def cleanHTML(sHTML):
    sHTML = sHTML.replace("<li>", "") # for now, this is a way to convert lists to sentances
    sHTML = sHTML.replace("</li>", ".")
    oSoup = BeautifulSoup(sHTML, "html5lib") # BeautifulSoup the html!
    [s.extract() for s in oSoup('head')] # remove everything in <head> tag
    [s.extract() for s in oSoup('script')] # remove everything in <script> tags
    [s.extract() for s in oSoup('noscript')] # remove everything in <noscript> tags
    sText = oSoup.text # get raw text left in article
    sText.lower() # convert any uppercase letters to lowercase
    sText = re.sub(r'\s+', ' ', sText) # clean up all the leftover whitespace with just a single space
    sText = sText.encode('utf-8')
    return sText