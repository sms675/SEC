# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 14:02:35 2017
Paste this:
CIK_code =  '0001166126'    
data = {'CIK': CIK_code}
fr = scrapy.FormRequest.from_response(response, formid='fast-search', formdata = data)
fetch(fr)

table1_loc = '/html/body/div[4]/div[4]/table'
relative_link = response.xpath(table1_loc + '/tr[' + str(2) + ']/td[2]/a/@href').extract_first()
absolute_link = 'https://www.sec.gov' + str(relative_link)
fetch(absolute_link)

table2_loc = '/html/body/div[4]//div//div//table[contains(@summary, "Document Format Files")]'

final_doc = str(response.xpath(table2_loc + '/tr[' + str(2) + ']/td[3]/a/@href').extract_first())
final_absolute_link = 'https://www.sec.gov' + str(final_doc)
fetch(final_absolute_link)

table_loc = '/html/body/div[4]/div[4]/table'  # location of table in new link

@author: stephen
"""
import os
import re
import scrapy
import sys
#import module to connect to postgresql
import psycopg2
from cleanHTML import cleanHTML
from scrapy.crawler import CrawlerProcess

#    
##creates new directory to store output files if folder is missing
#if not os.path.exists(output_dir):
#   os.makedirs(output_dir)

class SecSpider(scrapy.Spider):
    from secret_settings import *
    #from secret_settings import cleanHTML
    name = 'sec_spider'
    allowed_domains = ['www.sec.gov']
    login_url = 'https://www.sec.gov/edgar/searchedgar/companysearch.html'
    start_urls = [login_url]
    output_dir = '/home/stephen/Desktop/ETNfiles'
    pg_count = 0
    max_pg_scrape = 4
    # Fills in CIK field in start url.. build GUI to fill this in
    def parse(self, response):
        CIK_code =  '0001166126'    
        data = {'CIK': CIK_code}
        return [scrapy.FormRequest.from_response(response, formid ='fast-search', formdata = data, callback = self.parse_docs)]
	
    #counts and extracts document links from followed link : 
    #https://www.sec.gov/cgi-bin/browse-edgar?owner=exclude&action=getcompany&Find=Search&CIK=0001166126
    def parse_docs(self,response): 
        #Cycle through each document filing in the table... 42 is max
        self.pg_count += 1
        if self.pg_count == self.max_pg_scrape:
            print 'Page limit reached, closing program'
            quit()
        for newlink in range(2,42):  
            #location of table in new link
            table1_loc = '/html/body/div[4]/div[4]/table'  
            #relative link of document location
            relative_link = response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[2]/a/@href').extract_first()
            absolute_link = 'https://www.sec.gov' + str(relative_link)
            
            
            #stores filing name of link
            filing = str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[1]/text()').extract()[0]) 
            #stores description of link, accounts for exceptions when there is only one line of description
            try:
                description = (str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[3]/text()').extract()[0]) + 
                                   response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[3]/text()').extract()[1].encode('utf-8'))
            except  UnicodeEncodeError:
                print("Description Exception")
            #stores filing date
            filing_date = str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[4]/text()').extract()[0])
            #stores file number
            try:
                filenum = (str(response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[5]/a/text()').extract()[0]) +
                           response.xpath(table1_loc + '/tr[' + str(newlink) + ']/td[5]/text()').extract()[0].encode('utf-8'))
            except IndexError:
                filenum = 'undefined'
            
            next_page_loc = '/html/body/div[4]//div/form/table/tr//td/input\
                             [contains(@value, "Next 40")]'
                             
            next_page_link = 'https://www.sec.gov' + str(response.xpath(next_page_loc).extract_first()[63:-3])             
                
            #makes a list of all the stored information
            doc_info = [absolute_link,filing,description,filing_date,filenum,next_page_link]
            
            #requests next link in sequence.
            request = scrapy.Request(absolute_link, callback = self.parse_file)
            
            #sends all stored information from this webpage to the next requested page
            request.meta['doc_info'] = doc_info

            yield request
        
        
    #Looks for sub document links and info from each document previously scraped, sends final request
    def parse_file(self,response):
        #location of new (final) table
        #use keyword 'document format files' to find the correct table in a robust fashion
        table2_loc = '/html/body/div[4]//div//div//table[contains(@summary, "Document Format Files")]'
        #counts size of table for for loop
        doc_count = len(response.xpath(table2_loc +'/tr').extract())
        #stores all info from previous link into final_info
        final_info = response.meta['doc_info']                
        
        for table_val in range(2,doc_count):
            #gets relative string of final document 
            final_doc = str(response.xpath(table2_loc + '/tr[' + str(table_val) + ']/td[3]/a/@href').extract_first())
            #only do something if the file extension is .txt or .htm.
            if (final_doc[-3:] == 'txt'or final_doc[-3:] == 'htm'):
                final_absolute_link = 'https://www.sec.gov' + str(final_doc)
                sub_description = str(response.xpath(table2_loc + '/tr[' + str(table_val) + ']/td[2]/text()').extract_first())
                doc_name = str(response.xpath(table2_loc + '/tr[' + str(table_val) + ']/td[3]/a/text()').extract_first())    
                print 'Found file: %s' % (doc_name)
                #add sub_description to final_info passed from previous link                
                final_info.append(sub_description)
                final_info.append(doc_name)
                request = scrapy.Request(final_absolute_link, callback = self.to_text)
                request.meta['total_description'] = final_info               
                yield request
            
            
    def to_text(self, response):
        
        doc_url = response.url
        doc_html = response.body        
        doc_html = re.sub(r'\s+', ' ', doc_html) # clean up all the leftover whitespace with just a single space
        doc_txt = cleanHTML(doc_html)

        total_description = response.meta['total_description']
        tots = total_description
             
        conn = psycopg2.connect("dbname=SEC user=postgres")
        cur = conn.cursor()
        cur.execute("SELECT MAX(id) from sec_filings;")
        max_id = cur.fetchone()
        if max_id[0] is None: # if no max then start from 1
            id_num = 0
            print "No max id, start from 1"
        else:
            id_num = max_id[0]
            
        id_num += 1
        #Fill querys
        print 'checking for repeats in primary key (url)...'
        try:
            cur.execute("INSERT INTO sec_filings (id,doc_url,doc_name,doc_type,doc_html,doc_text,\
            filing_date,file_num,filing,description,filing_url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s\
            ,%s,%s)",(id_num,doc_url,tots[7],tots[6],doc_html,doc_txt,tots[3],tots[4],tots[1],tots[2],tots[0]))
            conn.commit()
        except psycopg2.IntegrityError:
            print 'Integrity Error so filing discarded...'
            conn.commit()    
        
        cur.close()
        conn.close()
            
        print 'Doc_count: %s\n' % (id_num)
        print 'Filing_url: %s\n' % (tots[0]) 
        print 'Filing: %s\n' % (tots[1]) 
        print 'Description: %s\n' % (tots[2])
        print 'Filing_date: %s\n' % (tots[3])
        print 'File_num: %s\n' % (tots[4])
        print 'Next pg url: %s\n' % (tots[5])
        print 'Doc_type: %s\n' % (tots[6])
        print 'Document Name: %s\n' % (tots[7])
        
        
        #rather than saving the file, input into database using full url as key.
        #save file:
        #html_filename = os.path.join(self.output_dir, str(tots[7]))
        #txt_filename = os.path.join(self.output_dir, str(self.doc_count) + '_txt.html')        
        #with open(html_filename, 'wb') as f:
        #    f.write(doc_html)
        #with open(txt_filename, 'wb') as f:
        #    f.write(doc_txt)
        #make read-only
        # os.chmod(filename, 0555)
        
        next_page_link = tots[5]
        request = scrapy.Request(next_page_link, callback = self.parse_docs)
        return request

         
   
process = CrawlerProcess()
process.crawl(SecSpider)
process.start() 
