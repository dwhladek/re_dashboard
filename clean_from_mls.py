
# coding: utf-8

# # Geocoding, cleaning

# In[1]:


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


# In[2]:


# for single 
data = pd.read_csv('data_to_combine/11-2-18_with_lat_long_needs_cleaning.csv')


# In[4]:


# for multiple csv loads
# pull all the data csv files taken from the mls
filenames = glob.glob('*.csv')
file_dict= {i: pd.read_csv(i) for i in filenames}
for key,val in file_dict.items():
    exec(key[:-4] + '=val')
    
south_oc_housing = df1.append([df2, df3,df4...], ignore_index=True)


# In[ ]:


south_oc_housing = df1.append([df2, df3,df4...], ignore_index=True)
data = south_oc_housing.copy()


# ### DELETE DUPLICATES EARLY
# - make sure there are no index numbers in the data(nothing unique)

# In[61]:


# sometimes the df will have some variation of this
# make sure it is deleted beofre you look for duplicates
data.drop(['unnamed: 0'], axis=1, inplace=True)


# In[544]:


# check duplicates but make sure there are no index numbers when you run it(unique values)
data.duplicated().sum(), data.duplicated(subset=['listing_id', 'contract_status_change_date']).sum()


# In[545]:


data.drop_duplicates(subset=['listing_id', 'contract_status_change_date'], keep='first', inplace=True)
data = data.reset_index(drop=True)


# In[546]:


all_data.duplicated().sum()


# ### Adding lat and lon columns(for graphing)

# In[547]:


data.city.replace({'MV' : 'Mission Viejo', 'RSM': 'Rancho Santa Margarita', 'LD': 'Ladera Ranch', 'RMV': 'Rancho Mission Viejo', 'TC': 'Trabuco Canyon'}, inplace=True)


# In[548]:


data.city.value_counts()


# In[549]:


# create column with state filled in with CA(this is for the geocode api call)
data['state'] = 'CA'


# In[67]:


# since the api call does not worth with condo numbers
# need to create a new column to pull from(want to keep the condo number in original address for later)
# here we are saying replace any numbers with nothing and replace any instance of # with nothing
data['st_name_only'] = data['st_name'].str.replace('\d+', '').str.replace('\#','')


# In[68]:


# strip st_name of trailing whitespace
data.st_name_only = data.st_name_only.str.strip()
# list for ease
geocode_cols = list(['st#', 'st_name_only','city','state'])
#create column that is just like the one necessary for geocode
data['geocode_address'] = data[geocode_cols].apply(lambda x: '+'.join(x.astype(str)), axis=1)


# In[69]:


# replace whitespace with a '+'
data['geocode_address'] = data['geocode_address'].str.replace(' ','+')


# In[72]:


# code good for now. dont want to repeat it
import requests
#url initialized
url = 'https://maps.googleapis.com/maps/api/geocode/json?address='
# my PRIVATE api key
api = '######'
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


# In[73]:


len(geo_data['loc'])


# In[75]:


geo_data['loc']


# In[76]:


loc_data = pd.DataFrame(geo_data['loc'], columns=['lat', 'lon'])
loc_data.head()


# In[77]:


# join the lats and lons to the master df
data.join(loc_data)


# In[78]:


# if the above works do it for real
data = data.join(loc_data)


# In[79]:


data.head()


# ### The cleaning stage
# - We have created an mls archive with all the data we have since 2015. 
# - Now we need to clean the data so it contains all the information we are going to receive from the emails. 
# 

# #### Available fields:
#     - Full address(break up)
#     - price
#     - listing_id
#     - Status
#     - Sqft
#     - Bd/Ba (split up)
#     - Pool
#     - view
#     - yrbuilt
#     - type
#     - garage (which we dont have here)
# **Fields to add**
#     - lat & lon
#     - dom(subtract dt.today from date)
# 

# In[20]:


# in case you need to lower the columns again
#data.columns = data.columns.str.replace(' ', '_').str.lower()


# In[14]:


#all_data['is_duplicate'] = all_data.duplicated(subset=['listing_id'])
#all_data['is_duplicate'].value_counts()
#data.loc[(data.is_duplicate) == True]
#data = data[data['is_duplicate'] == True]
#data.drop_duplicates(subset=['Listing ID'],keep='first', inplace=True)


# ####  DROP THE FOLLOWING 
#         - ac/lsqft
#         - bac
#         - lsqft/ac
#         - mls
#         - mls area
#         - slc

# In[551]:


data.drop(['ac/lsqft', 'bac', 'lsqft/ac', 'mls', 'mls_area', 'slc'], axis=1, inplace=True)


# ### what to do next:
#     - Note there are no floats in the bath section of the email. a 2.5 bath will be 3. 
#     - split dom and cdom, delete cdom
#     - sqft split at / and take [0]
#     - yr built split at / and take [0]
#     - sub type split at / and take both. both type and the A/D are important(attached/detached)

# In[558]:


# splitting up all the things that need to be split. creating sep dataframes out oft hem
bed = pd.DataFrame(data['br/ba'].str.split('/').tolist(), columns =['bed','bath'])
dom = pd.DataFrame(data['dom/cdom'].str.split('/').tolist(), columns=['dom', 'cdom'])
sqft = pd.DataFrame(data['sqft'].str.split('/').tolist(), columns=['sqft_keep', 'delete1'])
yr = pd.DataFrame(data['yrbuilt'].str.split('/').tolist(), columns =['yrbuilt_keep', 'delete2'])
sub = pd.DataFrame(data['sub_type'].str.split('/').tolist(), columns=['type', 'a/d'])


# In[559]:


bed.tail()


# In[560]:


# list of dataframes to join
dfs = [data,bed,dom,sqft,yr,sub]
data = reduce((lambda df1,df2: pd.concat([df1,df2], axis=1)), dfs)


# In[561]:


data.tail()


# In[562]:


# drop the columns we dont need anymore
data.drop(data[['sub_type', 'br/ba', 'sqft', 'dom/cdom', 'yrbuilt', 'delete1', 'delete2','cdom' ]], axis=1, inplace=True)


# In[563]:


#need to strip price and price_sqft to get rid of the '$'
data['price'] = data['l/c_price'].str.replace('$','')
data['price'] = data['price'].str.replace(',','')
data['price_per_sqft'] = data['price_per_square_foot'].str.replace('$','').str.replace(',','')


# In[564]:


data = data.rename(columns ={'sqft_keep':'sqft', 'yrbuilt_keep':'yrbuilt', 's':'status', 'l/c_price':'display_price', 'price_per_square_foot': 'display_price/sqft', 'pool_private_yn':'pool', 'view_yn':'view'})


# In[565]:


def to_numeric(df,cols):
    for col in cols:
        df[col] = pd.to_numeric(df[col])
to_numeric(data, ['yrbuilt', 'sqft', 'dom', 'bed', 'price', 'price_per_sqft'])


# In[566]:


# what else to do
# 1. split date up and get a year, month, day column
# 2. Then change contract_status_chage_update to datetime
        #- get day of the week
# 3. split baths up into full, 3/4, 1/2, 1/4
# 4. fill in nans for:
    # - a/d
    # - view_yn
    # - pool_private_yn
# 5. Check datatypes


# In[690]:


#checkpoint
data_clean1 = data.copy()


# In[691]:


# 1. split date up and get a year, month, day column
dates = pd.DataFrame(data_clean1['contract_status_change_date'].str.split('/').tolist(), columns =['month','day', 'year'])
#combine the dataframe created above to the master df
data_clean1 = pd.concat([data_clean1,dates], axis=1)


# In[692]:


# 2. change to datetime so we can do functions like max, etc on it
data_clean1['contract_status_change_date'] = pd.to_datetime(data_clean1.contract_status_change_date)
# get day of week for analysis
data_clean1['day_of_week'] = data_clean1.contract_status_change_date.dt.weekday_name


# In[693]:


# 3. split baths up into full, 3/4, 1/2, 1/4
baths = pd.DataFrame(data_clean1['bath'].str.split(',').tolist(), columns =['full_bath','3/4_bath', '1/2_bath', '1/4_bath'])
data_clean1.dropna(subset=['bath'], inplace=True)
data_clean1 = data_clean1.join([baths])
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


# In[ ]:


#changing years to 2000s
data_clean1['year'] = data_clean1['year'].replace({18:2018, 16:2016, 17:2017, 15:2015, 19:2019})


# In[694]:


# 4. fill in nans for:
    # - a/d
    # - view_yn
    # - pool_private_yn


# In[695]:


# fill in nans a/d
data_clean1['a/d'] = np.where((data_clean1['a/d'].isnull()) & (data_clean1['type'] =='SFR'), 'D', data_clean1['a/d'])
data_clean1['a/d'] = np.where((data_clean1['a/d'].isnull()) & (data_clean1['type'] !='SFR'), 'A', data_clean1['a/d'])
# fill in nans for view_yn
data_clean1['view'] = np.where(data_clean1.view.isnull(), 'N', data_clean1['view'])
# fill in nans for pool_private_yn
data_clean1['pool'] = np.where(data_clean1.pool.isnull(), 'N', data_clean1['pool'])


# In[696]:


data_clean1.head()


# In[697]:


# Changing Datatypes
# month day and year to numeric
# pool and view to bool
# status, type, a/d, to category


# In[ ]:


data.month.replace({1: 'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7: 'Jul',8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}, inplace=True)


# In[698]:


# month day and year to numeric
to_numeric(data_clean1, ['month', 'day', 'year'])


# In[699]:


def to_cat(df, cols):
    for col in cols:
        df[col] = df[col].astype('category')

to_cat(data_clean1, ['status', 'type', 'a/d'])


# In[700]:


data_clean1 = data_clean1.drop(data_clean1[data_clean1['year'] <15].index)
data_clean1 = data_clean1.reset_index(drop=True)


# In[701]:


data_clean1['pool'] = data_clean1['pool'].map({'Y':True, 'N': False})
data_clean1['view'] = data_clean1['view'].map({'Y': True, 'N': False})
# for ease I want to be able to call address in the dash
data_clean1['address'] = data_clean1['st#'] + ' ' + data_clean1.st_name


# In[241]:


# upload data to csv data_for_upload[date].csv, index=False
data_clean1.to_csv('data_for_upload_01-13-19.csv', index=False)

