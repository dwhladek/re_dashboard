from datetime import datetime
import datetime as dt
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
import plotly.graph_objs as go
from plotly import plotly
import plotly.offline as offline
offline.init_notebook_mode()
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from flask import Flask
mapbox_access_token = 'pk.eyJ1IjoicGVhbnV0YnVkZGhhIiwiYSI6ImNqcWcwNnJodjAzM3U0NXM0d3lqbTRubmsifQ.buuqPb5XOC53Obg-IPSlZA'


data = pd.read_csv('data_for_upload_01-13-19.csv', parse_dates=['contract_status_change_date'])

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# these are for python anywhere servers
# server = Flask(__name__)
#app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=server)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


cities_list = [i for i in data['city'].unique()]

#axis_list = 


# creates an html table to fit inside one of our return callbacks
# borrowed generate_table from the plotly dash layout examples
def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +
        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))],
        style ={'text-align':'center', 'display':'inline-block'}
    )

#Creates the first div, the map and the table. All active data
def get_data(value):
    #getting df back where city = tab chosen and the property is active
    df_a = data.loc[(data['city'] == value) & (data['status'] == 'A')]
    #getting df back where city = tab chosen and the property is under contract or pending (lump them together for simplicity)
    df_u = data.loc[(data['city']== value) & ((data['status'] == 'U') | (data['status'] == 'P'))]
    # TABLE 
    # pivot the data on city with the specified tables to get min, mean and max on it then transpose(columns to rows)
    df_table = pd.pivot_table(df_a[['bath', 'bed','city', 'dom', 'sqft', 'price_per_sqft', 'price', 'yrbuilt']], index=['city'],aggfunc=[min,np.mean, max]).T
    # df was multiIndexed, meaning it had min, avg, and max as first index, then the features as the second. to change this we unstack it
    # unstack on the first multiIndex(min, avg, max). This moves those rows into columns
    df_table = df_table.unstack(0)
    # reset index on the value(city), this gets rid of the city multiIndex. Now we have the setup we want, Features(sqft, beds, etc) as rows, and min, mean, max as the columns
    # Then I sorted the values because it looked better to have price and sqft on top of the table
    df_table = df_table[value].reset_index().sort_values('max', ascending=False)
    # label the columns the way you want them. The first is a space because I want that column to be empty space. 
    # It looks way better on the table on the site
    df_table.columns = [' ', 'Minimum', 'Average', 'Maximum']
    # replace the features values, or ' ' values with something more user friendly
    df_table[' '] = df_table[' '].replace({'price': 'Listing Price', 'sqft':'SqFt', 'yrbuilt':'Year Built', 'price_per_sqft': 'Price Per SqFt',
                                            'dom':'Days on Market', 'bed':'Beds', 'bath':'Baths'})
    # round the average column. Its the only one that has wild float numbers
    df_table['Average'] = df_table.Average.round(0)
    # adding dollar sign to the price and price_per_sqft_ column. remember we created a column that is just empty space
    for col in [col for col in df_table if col != ' ']:
        # where the features column contains price add $ to the front and replace the .0 at the end of the string. if the value in features
        # does not have price in it, keep the value
        # remember we created a column that is an empty space
        df_table[col] = np.where(df_table[' '].str.contains('Price'), ('$' + df_table[col].astype(str)).str.replace('\.0',''), df_table[col])
        # now I return what is presented on the website based on the tab selection
    return html.Div([
                # h3 heading that includes a call to the tab choice(value)
                html.H3('Current Listings in {}'.format(value)),
                # starting a new div
                html.Div([
                    # h6 heading
                    html.H6('There are {} houses for sale and {} houses in escrow'.format(len(df_a), len(df_u))),
                    # dash core component graph from plotly dash 
                    dcc.Graph(
                        # id if it needs to be called 
                        id='active_map',
                        # creates the plotly figure dict, the data and layout
                        figure={
                        # data portion of the plot which is the visualization information
                        'data' : [
                        # plotly call for the map 
                        go.Scattermapbox(
                            # latitude of active df
                            lat= df_a['lat'],
                            # longitude of active df
                            lon=df_a['lon'],
                            # what to put on the map
                            mode='markers',
                            # the size and color of the marker
                            marker=dict(size=9,
                                        color='green'
                                        ),
                            # text on hover(cannot figure out how to put 2 pieces of text in there)
                            text = df_a['address'],
                            # what to show on hover, we show what is above
                            hoverinfo='text',
                            # name of the map
                            name='Active'
                        ),
                        go.Scattermapbox(
                            lat = df_u['lat'],
                            lon=df_u['lon'],
                            mode='markers',
                            marker=dict(size=9,
                                        # yellow because in escrow
                                        color='yellow'
                                        ),
                            text= df_u['address'],
                            hoverinfo='text',
                            name='In Escrow'
                        ),],
                        'layout' : go.Layout(
                                # margin here sets the padding around the graph
                                 margin= dict(
                                    # the smaller the t value the less the padding
                                    t=50),
                                #title= 'There are {} houses for sale and {} houses in escrow'.format(len(df_a), len(df_u)),
                                # height of the graph in pixels
                                height = 600,
                                #  mode for mouse hovering, closest to cursor
                                hovermode='closest',
                                # mapbox specifc call
                                mapbox=dict(
                                    # accessing mapbox token
                                    accesstoken=mapbox_access_token,
                                    bearing=0,
                                    # lat and lon of the center of the map
                                    center=dict(
                                        lat=33.606388,
                                        lon=-117.657196
                                    ),
                                    pitch=0,
                                    zoom=10,
                                    # many styles
                                    style='dark'
                                ),

                            )

                        }
                    )# css styling, splitting the div in to 2 separate columns with width : 49% and display: inline-block 
                ], style = {'width': '49%', 'display':'inline-block', 'vertical-align':'middle', 'text-align':'center'}),
                html.Div([
                    # header 6
                    html.H6('Summary Statistics for Active Properties'),
                    # create the table with the function we defined above, and the df we manipulated above
                    generate_table(df_table),
                    # css styling, splitting the div in to 2 separate columns with width : 49% and display: inline-block 
                ], style = {'width': '49%', 'display':'inline-block', 'vertical-align':'middle', 'text-align':'center'}
                ),
                # mostly for aligning the header
            ], style={'text-align':'center'}
            )

#This function creates the histogram in which you pick a year 
# NOTE THIS HAS city_choice(tab city choice)
def histo_data(city_choice,year):
    # year comes in as a string, but in the df its type is an integer, so in order to compare we have to convert it here
    year = pd.to_numeric(year)
    # creating dataframe with users options, and making sure the properties are SOLD
    # REMEMBER city_choice MUST BE CALLED IN EACH CALLBACK
    df_sold_yearly = data.loc[(data.year == year) & (data.city == city_choice) & (data.status == 'S')]
    # making bar graph friendly dataframe so its easy to call in the graph below. also using contract_status_change_date: max so the months are in order
    df_sold_bar = df_sold_yearly.groupby('month', as_index=False).agg({'city':'count', 'contract_status_change_date': 'max'}).sort_values('contract_status_change_date')
    return html.Div([
                html.H5('Number of Houses sold per month in {}'.format(year)),
                # calling the dash graph again
                dcc.Graph(
                    id = 'yearly_hist',
                    figure={
                        'data' : [
                            # bar graph
                            go.Bar(
                                # x = the months in the year
                                x= list(df_sold_bar['month'].values),
                                # y data is the count of those values per month(used city as a fill in for count)
                                y = list(df_sold_bar.city.values),
                            )
                        ],
                        'layout' : 
                            go.Layout(
                                margin= dict(
                                    t=50),
                                xaxis=dict(
                                        title = 'Month'
                                ),
                                yaxis = dict(
                                    title= 'Number of Houses sold'
                                ),
                            )
                        })
                ])


def scatter_data(city_choice, month, year_for_scatter,yaxis, xaxis, hue_for_scatter):
    # change year to numeric!!!!
    year = pd.to_numeric(year_for_scatter)
    # 
    df1 = data.loc[(data.year == year) &(data.city == city_choice) & (data.status == 'S') ]
    return html.Div([
        dcc.Graph(
            id = 'scatter_plot', 
            figure={
                'data': [
                    go.Scatter(
                        x = df1[xaxis],
                        y = df1[yaxis],
                        text=data['address'],
                        mode= 'markers',
                        marker={
                            'size': 8,
                            'opacity': 0.5,
                            'line': {'width': 0.5, 'color': 'white'}
                        }
                    )
                ],
                'layout' : 
                    go.Layout(
                        margin=dict(
                            t=50),
                        xaxis=dict(
                            title = '{}'.format(xaxis)
                            ),
                        yaxis = dict(
                            title= '{}'.format(yaxis)
                            ),
                    )
            }
        )
    ])

app.layout = html.Div([
                html.H4('South Orange County Housing'),
                # Setting up the tabs for the user to choose
                # There has to be a way to do this better
                dcc.Tabs(id='city_choice_tabs', value=cities_list[0], children = [
                    dcc.Tab(label=cities_list[0], value=cities_list[0]),
                    dcc.Tab(label=cities_list[1], value=cities_list[1]),
                    dcc.Tab(label=cities_list[2], value=cities_list[2]),
                    dcc.Tab(label=cities_list[3], value=cities_list[3]),
                    dcc.Tab(label=cities_list[4], value=cities_list[4])
                    ]),
                #output
                html.Div(id='city_content'),
                html.Div([
                    html.H3('Sold Properties'),
                ],      style ={'text-align':'center'}
                ),
                html.Div([       
                    html.H6('Pick a year'),
                    # drop down choice for year
                    dcc.Dropdown(
                        id='year',
                        # creating a loop for the auctions. this allows me to add data with any year and not have to worry about updating the code
                        options=[{'label':i, 'value':i} for i in data['year'].unique()],
                        # initial/starting value
                        value ='2018'
                ),
                html.Div(id='sold_content'),
                ], style = {'width': '49%', 'display': 'inline-block'}),
                html.Div([
                    html.H5('Explore it yourself'),
                    dcc.RadioItems(
                        id ='year_for_scatter',
                        options=[{'label': i, 'value':i} for i in data['year'].unique()],
                        value='2018',
                        labelStyle={'display':'inline-block'}
                    ),
                    html.H6('Choose a year and month(s)'),
                    dcc.Checklist(
                        id='month',
                        options=[{'label': i, 'value':i} for i in data['month'].unique()],
                        values = 'Jan',
                        labelStyle={'display':'inline-block'}
                    ),
                    html.Div([
                        html.H6('X-Axis'),
                    dcc.Dropdown(
                        id='xaxis',
                        options = [{'label': 'Price', 'value':'price'}, 
                                  {'label' : 'Price Per Sqft', 'value':'price_per_sqft'},
                                  {'label': 'Days on Market', 'value': 'dom'},
                                  {'label':'Square Footage', 'value': 'sqft'},
                                  {'label': 'Year Built', 'value': 'yrbuilt'}],
                        value='sqft'
                    ),
                    ], style= {'width': '49%', 'display': 'inline-block'}
                    ),
                    html.Div([
                        html.H6('Y-Axis'),
                    dcc.Dropdown(
                        id ='yaxis',
                        options =[{'label': 'Price', 'value':'price'}, 
                                  {'label' : 'Price Per Sqft', 'value': 'price_per_sqft'},
                                  {'label': 'Days on Market', 'value': 'dom'},
                                  {'label':'Square Footage', 'value': 'sqft'},
                                  {'label': 'Year Built', 'value': 'yrbuilt'}],
                        value = 'price'
                    ),
                    ], style={'width': '49%', 'display':'inline-block', }
                    ),
                # output div
                html.Div(id ='scatter_content'),
                ], style = {'width': '49%', 'display': 'inline-block', 'text-align':'center'}
            ),
        ])
# First callback. note that the first part of the tuple in output(city_content) never gets explicitly called again after this.
# it is assumed that after every @app.callback, the function immediately following is the html that is returned.
#output is city_content which we defined above as the output for the tabs
@app.callback(dash.dependencies.Output('city_content', 'children'),
                # making the input the tabs pick(city choice)
                [dash.dependencies.Input('city_choice_tabs', 'value')])
# this is the function returns html given the user input
# this function takes 1 arg, city_choice, which is the tab selection. 
def render_content(city_choice):
    return html.Div([
            # this function returns a div that has the function get_data(city_choice) which we've defined
            get_data(city_choice)])

# second callback outputting the sold content which we have defined above as the output for the year dropdown
@app.callback(dash.dependencies.Output('sold_content', 'children'),
            #NOTE WE CALL IN THE CITY CHOICE TABS AGAIN. we need to make sure to reference it to make sure we are assigning the data 
            # according to the correct tab choice
            [dash.dependencies.Input('city_choice_tabs', 'value'),
            # input of the year drop down
            dash.dependencies.Input('year', 'value')])

def yearly_hist(year, city_choice):
    return html.Div([
        # here we call in the histo_data function we defined above
        histo_data(year, city_choice)
        ])

# third callback outputting the scatter-content which we have defined above
@app.callback(dash.dependencies.Output('scatter_content', 'children'),
             [dash.dependencies.Input('city_choice_tabs', 'value'),
             dash.dependencies.Input('month', 'values'),
             dash.dependencies.Input('year_for_scatter', 'value'),
             dash.dependencies.Input('yaxis', 'value'),
             dash.dependencies.Input('xaxis', 'value')])

def scatter_call(city_choice, month, year_for_scatter,yaxis, xaxis):
    return html.Div([
        scatter_data(city_choice, month, year_for_scatter,yaxis,xaxis)
        ])
#run it 
if __name__ == '__main__':
    app.run_server(debug=True)


