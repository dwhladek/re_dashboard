
# Geocoding, cleaning


import numpy as np
import glob
from scipy import stats
from scipy.stats import norm, skew
import pandas as pd
import datetime
import datetime as dt
import matplotlib.pyplot as plt
import io
import seaborn as sns

# needed to upload csv to colab
#from google.colab import files
#uploaded = files.upload()

# for single 
data = pd.read_csv('data_for_upload_01-13-19.csv')

# for multiple csv loads
# pull all the data csv files taken from the mls
filenames = glob.glob('*.csv')
file_dict= {i: pd.read_csv(i) for i in filenames}
for key,val in file_dict.items():
    exec(key[:-4] + '=val')
    
#south_oc_housing = df1.append([df2, df3,df4...], ignore_index=True)

#south_oc_housing = df1.append([df2, df3,df4...], ignore_index=True)
#data = south_oc_housing.copy()

"""### DELETE DUPLICATES EARLY
- make sure there are no index numbers in the data(nothing unique)
"""

# sometimes the df will have some variation of this
# make sure it is deleted beofre you look for duplicates
#data.drop(['unnamed: 0'], axis=1, inplace=True)

# check duplicates but make sure there are no index numbers when you run it(unique values)
data.duplicated().sum(), data.duplicated(subset=['listing_id', 'contract_status_change_date']).sum()

data.drop_duplicates(subset=['listing_id', 'contract_status_change_date'], keep='first', inplace=True)
data = data.reset_index(drop=True)

data.duplicated().sum()

"""### Adding lat and lon columns(for graphing)"""

data.city.replace({'MV' : 'Mission Viejo', 'RSM': 'Rancho Santa Margarita', 'LD': 'Ladera Ranch', 'RMV': 'Rancho Mission Viejo', 'TC': 'Trabuco Canyon'}, inplace=True)

data.city.value_counts()

# create column with state filled in with CA(this is for the geocode api call)
data['state'] = 'CA'

# since the api call does not worth with condo numbers
# need to create a new column to pull from(want to keep the condo number in original address for later)
# here we are saying replace any numbers with nothing and replace any instance of # with nothing
data['st_name_only'] = data['st_name'].str.replace('\d+', '').str.replace('\#','')

# strip st_name of trailing whitespace
data.st_name_only = data.st_name_only.str.strip()
# list for ease
geocode_cols = list(['st#', 'st_name_only','city','state'])
#create column that is just like the one necessary for geocode
data['geocode_address'] = data[geocode_cols].apply(lambda x: '+'.join(x.astype(str)), axis=1)

# replace whitespace with a '+'
data['geocode_address'] = data['geocode_address'].str.replace(' ','+')

# code good for now. dont want to repeat it
import requests
#url initialized
url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
# my PRIVATE api key
api = '#######'
#column to iterate over
col = data['geocode_address']
# dictionary to store lats and lons
geo_data = {}
# making appending easier to create a list inside the dict
geo_data['loc'] =[]
# loop over the length of the column
for i in range(len(col)):
    # using the requests library. we are getting the data from the url for each address in column
    results = requests.get(url + str(data['geocode_address'][i]) + api)
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

len(geo_data['loc'])

loc_data = pd.DataFrame(geo_data['loc'], columns=['lat', 'lon'])
loc_data.head()

# join location data with data df
data = data.join(loc_data)

"""### The cleaning stage
- We have created an mls archive with all the data we have since 2015. 
- Now we need to clean the data so it contains all the information we are going to receive from the emails.

#### Available fields:
    - Full address(break up)
    - price
    - listing_id
    - Status
    - Sqft
    - Bd/Ba (split up)
    - Pool
    - view
    - yrbuilt
    - type
    - garage (which we dont have here)
**Fields to add**
    - lat & lon
    - dom(subtract dt.today from date)
"""

# in case you need to lower the columns again
#data.columns = data.columns.str.replace(' ', '_').str.lower()

#all_data['is_duplicate'] = all_data.duplicated(subset=['listing_id'])
#all_data['is_duplicate'].value_counts()
#data.loc[(data.is_duplicate) == True]
#data = data[data['is_duplicate'] == True]
#data.drop_duplicates(subset=['Listing ID'],keep='first', inplace=True)

"""####  DROP THE FOLLOWING 
        - ac/lsqft
        - bac
        - lsqft/ac
        - mls
        - mls area
        - slc
"""
"""### what to do next:
    - Note there are no floats in the bath section of the email. a 2.5 bath will be 3. 
    - split dom and cdom, delete cdom
    - sqft split at / and take [0]
    - yr built split at / and take [0]
    - sub type split at / and take both. both type and the A/D are important(attached/detached)
"""

# splitting up all the things that need to be split. 
data[['bed', 'bath']] = pd.DataFrame(data['br/ba'].str.split('/').tolist())
data['dom'] = pd.DataFrame(data['dom/cdom'].str.split('/').tolist()).iloc[:,0]
data['sqft'] = pd.DataFrame(data['sqft'].str.split('/').tolist()).iloc[:,0]
data['yrbuilt'] = pd.DataFrame(data['yrbuilt'].str.split('/').tolist()).iloc[:,0]
data[['type', 'a/d']] = pd.DataFrame(data['sub_type'].str.split('/').tolist())

# drop the columns we dont need anymore
data.drop(data[['sub_type', 'br/ba', 'dom/cdom']], axis=1, inplace=True)

#need to strip price and price_sqft to get rid of the '$'
data['price'] = data['l/c_price'].str.replace('$','')
data['price'] = data['price'].str.replace(',','')
data['price_per_sqft'] = data['price_per_square_foot'].str.replace('$','').str.replace(',','')

data = data.rename(columns ={'s':'status', 'l/c_price':'display_price', 'price_per_square_foot': 'display_price_per_sqft', 'pool_private_yn':'pool', 'view_yn':'view'})

def to_numeric(df,cols):
    for col in cols:
        df[col] = pd.to_numeric(df[col])

to_numeric(data, ['yrbuilt', 'sqft', 'dom', 'bed', 'price', 'price_per_sqft'])

# what else to do
# 1. Then change contract_status_chage_update to datetime
        #- get day of the week
# 2. split baths up into full, 3/4, 1/2, 1/4
# 3. fill in nans for:
    # - a/d
    # - view_yn
    # - pool_private_yn
# 4. Check datatypes

#checkpoint
data_clean1 = data.copy()

# 1. change to datetime 
data_clean1['contract_status_change_date'] = pd.to_datetime(data_clean1.contract_status_change_date)
# get day of week for analysis
data_clean1['day_of_week'] = data_clean1.contract_status_change_date.dt.weekday_name
#get month 
data_clean1['month'] = [i.strftime('%b') for i in data_clean1['contract_status_change_date']]
#get year
data['year'] = pd.to_numeric(data.contract_status_change_date.dt.year)

# 2. split baths up into full, 3/4, 1/2, 1/4
data_clean1[['full_bath','3/4_bath', '1/2_bath', '1/4_bath']] = pd.DataFrame(data_clean1['bath'].str.split(',').tolist())
del data_clean1['bath']
# replace with necessary values so we can add them accurately
data_clean1['3/4_bath'] = data_clean1['3/4_bath'].replace(1,.75)
data_clean1['1/2_bath'] = data_clean1['1/2_bath'].replace(1,.5)
data_clean1['1/4_bath'] = data_clean1['1/4_bath'].replace(1,.25)
# changing to numeric so we can round the following line(would have to change to numeric anyway)
to_numeric(data_clean1, ['full_bath','3/4_bath', '1/2_bath', '1/4_bath'])
# adding the baths together and then rounding them(since the email gives us rounded numbers)
data_clean1['bath'] = round(data_clean1['full_bath'] + data_clean1['3/4_bath'] + data_clean1['1/2_bath'] + data_clean1['1/4_bath'], 0)
#drop the rows since we dont need them
data_clean1.drop(data_clean1[['full_bath', '3/4_bath', '1/2_bath', '1/4_bath']], axis=1, inplace=True)

# 3. fill in nans for:
    # - a/d
    # - view_yn
    # - pool_private_yn

# fill in nans a/d
data_clean1['a/d'] = np.where((data_clean1['a/d'].isnull()) & (data_clean1['type'] =='SFR'), 'D', data_clean1['a/d'])
data_clean1['a/d'] = np.where((data_clean1['a/d'].isnull()) & (data_clean1['type'] !='SFR'), 'A', data_clean1['a/d'])
# fill in nans for view_yn
data_clean1['view'] = np.where(data_clean1.view.isnull(), 'N', data_clean1['view'])
# fill in nans for pool_private_yn
data_clean1['pool'] = np.where(data_clean1.pool.isnull(), 'N', data_clean1['pool'])

data_clean1.head()

#4.  Changing Datatypes
# pool and view to bool
# status, type, a/d, to category

def to_cat(df, cols):
    for col in cols:
        df[col] = df[col].astype('category')

to_cat(data_clean1, ['status', 'type', 'a/d'])

def to_bool(df, cols):
  for col in cols:
    df[col] = df[col].map({'Y':True, 'N':'False'})
    
to_bool(data_clean1, ['pool', 'view'])


# for ease I want to be able to call address in the dash
data_clean1['address'] = data_clean1['st#'] + ' ' + data_clean1.st_name

data_clean1.drop(['geocode_address', 'st_name_only', 'day', 'st#', 'st_name','ac/lsqft', 'bac', 'lsqft/ac', 'mls', 'mls_area', 'slc'], axis=1, inplace=True)

# upload data to csv data_for_upload[date].csv, index=False
#data_clean1.to_csv('data_for_upload_01-13-19.csv', index=False)

