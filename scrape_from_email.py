# -*- coding: utf-8 -*-
"""scrape_from_email.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17TfB9rGQqkhx8x8j2z-Dx2oYNCd_BzaZ
"""

import numpy as np
import pandas as pd
import email, getpass, imaplib, os, re
import matplotlib.pyplot as plt
import datetime 
from datetime import date, timedelta
from bs4 import BeautifulSoup
import datetime as dt

# connect to gmail imap server
m = imaplib.IMAP4_SSL('imap.gmail.com')
# fill in username
username = '#######'
# fill in password
password = '######'
# login
m.login(username, password)

status,messages = m.select('re_dashboard')

if status != 'OK':
  print ('Inocrrect mailbox')
  
  exit()

print (messages)

# getting the ids for the emails that were received today. 
# needs to be in this format 
#yesterday = (date.today() - timedelta(1)).strftime('%d-%b-%Y')
df_date = date.today().strftime('%m/%d/%Y')
date = date.today().strftime('%d-%b-%Y')
resp, items = m.search(None, '(SENTON {date})'.format(date=date))
items = items[0].split()
#items = b','.join(items[0].split())
items

# looping over the emails we searched for above
props =[] 
for emailid in items:
  #temp_dict={}
  # fetching the items based on 
  resp, data = m.uid('fetch', emailid, '(RFC822)')
  email_body = data[0][1]
  mail = email.message_from_bytes(email_body)
  if mail.is_multipart():
    for part in mail.walk():
      body = part.get_payload(decode=True)
      soup = BeautifulSoup(str(body), 'html.parser')
      # this is finding all the tables with that certain style(each property has exactly 1 of these tables)
      breakdown = soup.find_all('table',{'style':'border-collapse:collapse;margin-bottom:2px'})
      #creating a list that contains a bs4.element for each property with all the information
      for i in breakdown:
        props.append(i)

alls = []
price =[]
for item in props:
  price.append(item.table('span', text=True))
for i in range(len(price)):
  alls.append([tag.text for tag in price[i]])

#date = date.today().strftime('%d-%b-%Y')
prop_dict={}
prop_dict['data']=[]
for i in range(len(alls)):
  prop_dict['data'].append({
      'full_address': alls[i][0],
      'display_price': alls[i][1], 
      'listing_id': alls[i][3],
      'status': alls[i][5],
      'sqft_all' : alls[i][7],
      'bed': alls[i][9],
      'bath': alls[i][10],
      'pool': alls[i][12],
      'view': alls[i][14],
      'yrbuilt': alls[i][16],
      'type': alls[i][18],
      'contract_status_change_date': df_date, 
      'state':'CA'
  })

props = pd.DataFrame(prop_dict['data'],columns=['full_address', 'display_price', 'listing_id', 'status', 'sqft_all', 'bed', 'bath', 'pool', 'view', 'yrbuilt', 'type', 'contract_status_change_date', 'state'])



#strip whitepspace
props1 = props1.applymap(lambda x: x.strip())
# creating streetname and city columns from address
props1[['address', 'city']]= pd.DataFrame(props1.full_address.str.split(',').tolist()).iloc[:, 0:2]
# getting sqft(first part of sqft_all)
props1['sqft'] = pd.DataFrame(props1.sqft_all.str.split().tolist()).iloc[:,0]
# attached or detached?
props1['a/d'] = np.where(props1.type =='SFR', 'D', 'A')
props1.head()

#getting geocode_address so that I can call google api for lat and lon
props1['st#'] = pd.DataFrame(props1['address'].str.split().tolist()).iloc[:,0]
props1['st_name_only'] = props1['address'].str.replace('\d+', '').str.replace('\#','')
geocode_cols = list(['st#', 'st_name_only','city','state'])
props1 = props1.applymap(lambda x: x.strip())
props1['geocode_address'] = props1[geocode_cols].apply(lambda x: '+'.join(x.astype(str)), axis=1)

# code good for now. dont want to repeat it
import requests
#url initialized
url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
# my PRIVATE api key
api = '#########'
#column to iterate over
col = props1['geocode_address']
# dictionary to store lats and lons
geo_data = {}
# making appending easier to create a list inside the dict
geo_data['loc'] =[]
# loop over the length of the column
for i in range(len(col)):
    # using the requests library. we are getting the data from the url for each address in column
    results = requests.get(url + str(props1['geocode_address'][i]) + api)
    # taking the data and making it a json
    json_data = json.loads(results.text)
    # appending lat and lon into the dictionary
    try:
        geo_data['loc'].append({
            # get the latitude
            'lat': json_data['results'][0]['geometry']['location']['lat'],
            # get the longitude
            'lon' : json_data['results'][0]['geometry']['location']['lng']
    })
    except:
        geo_data['loc'].append({
            # fill lat with 0 if error occurs
            'lat': 0,
            # fill lon with 0 if error occurs
            'lon' : 0
    })

loc_data = pd.DataFrame(geo_data['loc'], columns=['lat', 'lon'])
props1 = props1.join(loc_data)

props1['price'] = pd.to_numeric(props['display_price'].str.replace('$', '').str.replace(',',''))
props1['price_per_sqft'] = round(props1['price'] / pd.to_numeric(props1['sqft'].str.replace(',','')),2)
#want the display price so we can present it as a currency
props1['display_price_per_sqft'] = props1['price_per_sqft'].map("${:,.2f}".format)

# checkpoint
props2 = props1.copy()

# turn contract status date into datetime so we can pull info out of it
props2['contract_status_change_date'] = pd.to_datetime(props2.contract_status_change_date)
props2['day_of_week'] = props2.contract_status_change_date.dt.weekday_name
props2['month'] = [i.strftime('%b') for i in props2['contract_status_change_date']]
props2['year'] = props2.contract_status_change_date.dt.year
#change date format
props2['contract_status_change_date']= props2['contract_status_change_date'].dt.strftime('%m/%d/%Y')

# get rid of slash in bed
props2['bed'] = props2.bed.str.replace('/', '')

def to_bool(df, cols):
  for col in cols:
    df[col] = df[col].map({'Y':True, 'N':'False'})
    
to_bool(props2, ['pool', 'view'])

props2.drop(['sqft_all', 'st#', 'st_name_only', 'geocode_address', 'full_address'], axis=1, inplace=True)

# now we can send props2 to database

# filler. need to figure out how to keep dom updated. its an important metric
props2['dom'] = 1

props2

