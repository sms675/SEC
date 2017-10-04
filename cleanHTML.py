# -*- coding: utf-8 -*-
"""
Created on Tue Oct  3 14:48:13 2017

@author: stephen
"""



def cleanHTML(sHTML):
    from bs4 import BeautifulSoup
    import re
    sHTML = sHTML.replace("<li>", "") # for now, this is a way to convert lists to sentences
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
    
    
    