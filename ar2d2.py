#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import sqlite3
import base64
import xml.etree.ElementTree as etree
import requests
from pinder import Campfire, Room


# ***************************************************************************
# ***  Important! Here you need to enter data or write it to settings.py  ***
# ***************************************************************************
DB_file = ''
# for Codebase
CODEBASE_PROJECT_URL = ''
CODEBASE_USERNAME =''
CODEBASE_APIKEY = ''
# for Campfire
SECRET_TOKEN = ''
SUBDOMAIN = ''
ROOM_ID = ''
# ***************************************************************************

# if you want to keep confidential data separately
try:
    from settings import *
except:
    pass



# create DB if need
create = not os.path.exists(DB_file)
if create:
    db = sqlite3.connect(DB_file)
    cursor = db.cursor()
    cursor.execute('''create table Messages(
                my_id integer primary key autoincrement unique not null,
                title text,
                id text,
                timestamp text,
                type text,
                html_title text,
                html_text text
                )''')

    db.commit()
    cursor.close()



# load last activity
path = 'activity'
url = "%s/%s" % (CODEBASE_PROJECT_URL, path)
headers = {"Content-type": "application/xml",
           "Accept": "application/xml",
           "Authorization": "Basic %s" % base64.b64encode("%s:%s" % (CODEBASE_USERNAME,
                                                                     CODEBASE_APIKEY))}
r = requests.get(url, headers=headers)

# parse answer
tree = etree.parse(r)
root = tree.getroot()


db = sqlite3.connect(DB_file)
cursor = db.cursor()

# connect to Campfire
c = Campfire(SUBDOMAIN, SECRET_TOKEN, ssl=True)
room = c.room(ROOM_ID)
room.join()


for child in root:
    cursor.execute('select id from Messages where id=?', (child.findall('id')[0].text,))
    messages = cursor.fetchall()
    if messages:
        continue
    # write to DB
    my_data = (child.findall('title')[0].text,
               child.findall('id')[0].text,
               child.findall('timestamp')[0].text,
               child.findall('type')[0].text,
               child.findall('html-title')[0].text,
               child.findall('html-text')[0].text)
    cursor.execute('''insert into Messages (
                                        title,
                                        id,
                                        timestamp,
                                        type,
                                        html_title,
                                        html_text)
                    values (?, ?, ?, ?, ?, ?)''', my_data)
    db.commit()

    m = re.findall('a href="/.+?">', child.findall('html-title')[0].text)
    m = m[0].lstrip('a href="')
    m = m.rstrip('">')

    link = 'https://arvors.codebasehq.com%s' % m
    message = '%s \n %s' % (child.findall('title')[0].text, link)
    room.speak(message)
