#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import urllib.request
import json
import ssl
from bs4 import BeautifulSoup

class ftDB():

    def __init__(self, url):
        if url == '':
            raise ValueError('No doreen URL given')
            exit()
        if not url.endswith('/'):
            url = url + '/'
        self.base_url = url
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

    def call_server_json(self, call):
        print('Loading:' + self.base_url + call)
        data = json.loads(urllib.request.urlopen(self.base_url + call, context=self.ctx).read().decode('utf-8'))
        return(data)

    def call_server_html(self, call):
        print('Loading: ' + self.base_url + call)
        data = urllib.request.urlopen(self.base_url + call, context=self.ctx).read().decode('utf-8', 'replace')  # .replace('\n', '').split('drn-main-page">')[1].split('<!-- .drn-main.page -->')[0]
        return(data)

    def get_main_page_from_html(self, html):
        dom = BeautifulSoup(html.encode(), 'html.parser', from_encoding='utf-8')
        data = dom.find(None, {'class': 'drn-main-page'}).renderContents()
        return(data)

    def fulltext_search(self, search, page=1):
        call_string = 'api/tickets?fulltext=' + search
        if page != 1:
            call_string = call_string + '&page=' + str(page)
        data = self.call_server_json(call_string)
        return(data)

    def find_string_in_list(self, data, string):
        pos = 0
        while pos <= len(data) - 1:
            if string in str(data[pos]):
                return(str(data[pos]))
            else:
                pos += 1
        return(None)

    def get_ticket_data(self, id):
        web = self.call_server_html('ticket/' + str(id))
        main_page = self.get_main_page_from_html(web)
        data = {}
        dom = BeautifulSoup(main_page, 'html.parser', from_encoding='utf-8')
        data['title'] = dom.find(None, {'class': 'page-header'}).text.strip()
        rows = dom.findAll(None, {'class': 'row'}, recursive=False)
        # get description
        desc_html_str = self.find_string_in_list(rows, '<!-- begin row for description -->')
        if desc_html_str != None:
            desc_dom = BeautifulSoup(desc_html_str, 'html.parser')
            data['description'] = desc_dom.find(None, {'class': 'col-md-9'}).text.strip()
        image_html_str = self.find_string_in_list(rows, '<!-- begin row for ft_icon -->')
        if image_html_str != None:
            image_dom = BeautifulSoup(image_html_str, 'html.parser')
            data['image_id'] = image_dom.find(None, {'class': 'col-xs-9'}).renderContents().decode('utf-8', 'replace').split('thumbnail/')[1].split('?')[0]
        article_nos_html_str = self.find_string_in_list(rows, '<!-- begin row for ft_article_nos -->')
        if article_nos_html_str != None:
            article_nos_dom = BeautifulSoup(article_nos_html_str, 'html.parser')
            article_nos_dict = {}
            for line in article_nos_dom.find(None, {'class': 'col-xs-9'}).text.split('\n'):
                line_split = line.split(': ')
                article_nos_dict[line_split[0]] = line_split[1]
            data['article_nos'] = article_nos_dict
        parents_html_str = self.find_string_in_list(rows, '<!-- begin row for ft_contained_in -->')
        if parents_html_str != None:
            parents_dom = BeautifulSoup(parents_html_str, 'html.parser')
            parents_dict = {}
            for line in parents_dom.find(None, {'class': 'col-xs-9'}).renderContents().decode('utf-8', 'replace').split(', '):
                if 'href' in line:
                    parents_dict[line.split('ticket/')[1].split('"')[0]] = line.split('">')[1].split('</a>')[0]
            data['parents'] = parents_dict
        childs_html_str = self.find_string_in_list(rows, '<!-- begin row for ft_contains -->')
        if childs_html_str != None:
            data['has_childs'] = True
        else:
            data['has_childs'] = False
        return(data)

    def get_ticket_childs(self, part_id):
        basic_call_string = 'api/ft-partslist/' + str(part_id)
        page = 1
        partslist = []
        return_data = {}
        data = self.call_server_json(basic_call_string)
        if data['cTotal'] == 0:
            print('no childs')
            return({})
        total_pages = data['cPages']
        return_data['total'] = data['cTotalParts']
        return_data['total_unique'] = data['cTotal']
        partslist.append(data['results'])
        while page < total_pages:
            page += 1
            data = self.call_server_json(basic_call_string + '?page=' + str(page))
            partslist.append(data['results'])
        return_data['parts'] = partslist
        return(return_data)
