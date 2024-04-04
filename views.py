from django.shortcuts import render
import pyodbc
import pandas as pd
import time
from django.conf import settings
import plotly.express as px
from django.shortcuts import render
import requests
import json
from sodapy import Socrata

def map_view(request):
    start_time = time.time()
    conn = pyodbc.connect('Driver={sql server};'
                          'Server=dotazdevsqlee04;'
                          'Database=STARS;'
                          'Trusted_Connection=yes;'
                          )
    query = """
        SELECT 
        ROW_NUMBER() OVER (ORDER BY Latitude, Longitude) AS Row_Num,
            Latitude, 
            Longitude, 
        COUNT(*) AS Count
        FROM [STARSParkingViolations]
        where Latitude IS NOT Null AND Longitude IS NOT NULL
        GROUP BY Latitude, Longitude
    """
    df = pd.read_sql_query(query, conn)
    latitudes = df['Latitude'].tolist()
    longitudes = df['Longitude'].tolist()
    counts = df['Count'].tolist()
    end_time = time.time()  # End measuring time
    run_time = end_time - start_time  # Calculate run time

    print("Run time:", run_time, "seconds")  # Print run time to server console
    return render(request, 'map.html', {'latitudes': latitudes, 'longitudes': longitudes, 'counts': counts})

def connsql(request):
    geocoded_result = []
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    page_number = request.GET.get('page', 1)  # Default page number is 1

    start_time = time.time()  # Start measuring time

    conn = pyodbc.connect('Driver={sql server};'
                          'Server=dotazdevsqlee04;'
                          'Database=STARS;'
                          'Trusted_Connection=yes;'
                          )

    cursor = conn.cursor()

    # Count the total number of records within the specified date range
    count_query = "SELECT COUNT(*) FROM STARSParkingViolations"
    where_clause = ""
    params = []

    if start_date and end_date:
        where_clause = " WHERE ISSUE_DATE BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    # Add condition to filter out null values
    if where_clause:
        where_clause += " AND Latitude IS NOT NULL AND Longitude IS NOT NULL"

    cursor.execute(count_query + where_clause, params)
    total_records = cursor.fetchone()[0]

    # Calculate pagination parameters dynamically
    items_per_page = min(200000, total_records)  # Limit to 200,000 records
    offset = (int(page_number) - 1) * items_per_page

    # Construct the main query
    query = "SELECT VIOLATION_CODE, ISSUE_DATE, Latitude, Longitude FROM STARSParkingViolations"

    if where_clause:
        query += where_clause

    query += f" ORDER BY ISSUE_DATE OFFSET {offset} ROWS FETCH NEXT {items_per_page} ROWS ONLY"

    # Execute the main query
    cursor.execute(query, params)
    result = cursor.fetchall()

    # Fetch available years from your data
    available_years_query = "SELECT MIN(YEAR(ISSUE_DATE)) AS min_year, MAX(YEAR(ISSUE_DATE)) AS max_year FROM STARSParkingViolations WHERE YEAR(ISSUE_DATE) BETWEEN 2018 AND 2024"
    available_years_cursor = conn.cursor()
    available_years_cursor.execute(available_years_query)
    available_years_result = available_years_cursor.fetchone()

    min_year = available_years_result.min_year
    max_year = available_years_result.max_year
    available_years = list(range(min_year, max_year + 1))

    # Format the date range string
    date_range_str = f"{start_date} to {end_date}" if start_date and end_date else "No date range specified"

    for row in result:
        violation_code = row.VIOLATION_CODE
        issue_date = row.ISSUE_DATE
        latitude = row.Latitude if row.Latitude is not None else 'null'
        longitude = row.Longitude if row.Longitude is not None else 'null'

        geocoded_result.append({
            'violation_code': violation_code,
            'coordinates': (latitude, longitude),
            'issue_date': issue_date,
        })

    conn.close()

    end_time = time.time()  # End measuring time
    run_time = end_time - start_time  # Calculate run time

    print("Run time:", run_time, "seconds")  # Print run time to server console

    return render(request, 'map200.html', {'sqlserverconn': geocoded_result,
                                         'available_years': available_years,
                                         'min_year': min_year,
                                         'max_year': max_year,
                                         'total_records': total_records,
                                         'date_range': date_range_str})

def render_view(request):
    # Logic to retrieve data
    tiff_path = 'images/Violations_2019_ALL_proj.png'  # Assuming it's a PNG file based on the extension in your template
    tiff_url = settings.STATIC_URL + tiff_path
    
    data = {
        'tiff_url': tiff_url
    }
    return render(request, 'Render.html', data)
































def plotly_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    violation_codes = request.GET.getlist('violation_code')  # Get a list of selected violation codes
    boroughs = request.GET.getlist('borough')  # Get a list of selected boroughs
    start_time = time.time()
    #-----------------------------------------DATABASE CONNECTION-----------------------------------------
    conn = pyodbc.connect('Driver={sql server};'
                          'Server=dotazdevsqlee04;'
                          'Database=STARS;'
                          'Trusted_Connection=yes;'
                          )
    #-----------------------------------------QUERIES-----------------------------------------
    query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY Latitude, Longitude) AS Row_Num,
            Latitude, 
            Longitude, 
            VIOLATION_CODE,
            NTAName,
            CityCouncilDistrict,
            CommunityDistrict,
            Boro,
            COUNT(*) AS Count
        FROM [STARSParkingViolations]
        WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
    """
    borough_names = {
        'Q': 'Queens',
        'B': 'Brooklyn',
        'SI': 'Staten Island',
        'BX': 'Bronx',
        'M': 'Manhattan'
    }

    cursor = conn.cursor()
    count_query = "SELECT COUNT(*) FROM STARSParkingViolations"
    where_clauses = []
    params = []

    # Add conditions for start and end dates if they are provided
    if start_date and end_date:
        query += f" AND ISSUE_DATE BETWEEN '{start_date}' AND '{end_date}'"
        where_clauses.append("ISSUE_DATE BETWEEN ? AND ?")
        params.extend([start_date, end_date])
    # Add condition to filter out null values for latitude and longitude
    where_clauses.append("Latitude IS NOT NULL AND Longitude IS NOT NULL")

    # Add conditions for violation codes if they are provided
    if violation_codes:
        violation_codes_str = "', '".join(violation_codes)  # Join selected violation codes into a string
        query += f" AND VIOLATION_CODE IN ('{violation_codes_str}')"
        where_clauses.append("VIOLATION_CODE IN (" + ",".join(["?"] * len(violation_codes)) + ")")
        params.extend(violation_codes)
    
    # Add conditions for boroughs if they are provided
    if boroughs:
        boroughs_str = "', '".join(boroughs)  # Join selected boroughs into a string
        query += f" AND Boro IN ('{boroughs_str}')"
        where_clauses.append("Boro IN (" + ",".join(["?"] * len(boroughs)) + ")")
        params.extend(boroughs)
    
    # Construct the final SQL query
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY Latitude, Longitude, VIOLATION_CODE, Boro, NTAName, CityCouncilDistrict, CommunityDistrict"
    
    # Execute the query and read results into a DataFrame
    df = pd.read_sql_query(query, conn)

    # Sort the DataFrame by count in ascending order
    df = df.sort_values(by='Count', ascending=True)
    #-----------------------------------------GET YEARS-----------------------------------------
    min_year = 2015
    max_year = 2024
    available_years = list(range(min_year, max_year + 1))
    date_range_str = f"{start_date} to {end_date}" if start_date and end_date else "No date range specified"
    
    # Extract unique violation codes from the DataFrame
    # Extract all unique violation codes from the database
    all_violation_codes_query = "SELECT DISTINCT VIOLATION_CODE FROM STARSParkingViolations"
    all_violation_codes_cursor = conn.cursor()
    all_violation_codes_cursor.execute(all_violation_codes_query)
    all_violation_codes_result = all_violation_codes_cursor.fetchall()
    available_violation_codes = sorted([code[0] for code in all_violation_codes_result])
    
    all_boroughs_query = "SELECT DISTINCT Boro FROM STARSParkingViolations"
    all_boroughs_cursor = conn.cursor()
    all_boroughs_cursor.execute(all_boroughs_query)
    all_boroughs_result = all_boroughs_cursor.fetchall()
    available_boroughs = [borough_names.get(borough[0], borough[0]) for borough in all_boroughs_result]


    # Extract selected boroughs from the request
    selected_boroughs = request.GET.getlist('borough')

    # Filter out None values and then sort
    available_boroughs = sorted([borough[0] for borough in all_boroughs_result if borough[0] is not None])

    # Include selected boroughs in the SQL query
    if selected_boroughs:
        boroughs_str = "', '".join(selected_boroughs)
        query += f" AND Boro IN ('{boroughs_str}')"

#-----------------------------------------ID MAPPING-----------------------------------------
    violation_code_mapping = {
        '4': ['4A (no prmt)/4B (nonbus)'],
        '8': ['8'],
        '9': ['9'],
        '10': ['10'],
        '11': ['11'],
        '12': ['12'],
        '13': ['13', '13 (No Stand exc taxi stan)'],
        '14': ['14'],
        '16': ['16/16A (noncom)'],
        '17': ['17', '17/17A (EV only)'],
        '18': ['18'],
        '19': ['19'],
        '20': ['20(com)/20A(non-com)'],
        '21': ['21'],
        '22': ['22 (exc hotel load)'],
        '23': ['23'],
        '24': ['24'],
        '25': ['25'],
        '26': ['26'],
        '28': ['28'],
        '31': ['31'],
        '32': ['32 (missing meter)/32A(broken meter)'],
        '33': ['33'],
        '37': ['37'],
        #37 is jsut 37, change back
        '38': ['38'],
        '39': ['39'],
        '40': ['40'],
        '42': ['42'],
        '44': ['44'],
        '45': ['45'],
        '46': ['46 (com plate/46A(non-COM/46B(com-100ft)'],
        '47': ['47(com)/47A(angle pkg com)'],
        '48': ['48'],
        '49': ['49'],
        '50': ['50'],
        '51': ['51'],
        '52': ['52'],
        '53': ['53'],
        '54': ['54'],
        '58': ['58'],
        '59': ['59'],
        '60': ['60'],
        '61': ['61'],
        '64': ['64'],
        '65': ['65-O/T STD,Dpl/Con,30 Mn,D/S'],
        '66': ['66'],
        '67': ['67'],
        '68': ['68'],
        '69': ['69'],
        '81': ['81'],
        '82': ['82'],
        '85': ['85'],
        '86': ['86'],
        '87': ['87 (fradulent permit use)'],
        '89': ['89'],
        '98': ['98'],
        '99': ['Other']
    }
    #-----------------------------------------COLORS-----------------------------------------
    # Define color scale stops
    # color_scale_stops = [
    #     [0/4789, '#B9D9EB'],   # Lower values (light blue)
    #     [1/2400, '#ADD8E6'],   # 1% of the range
    #     [1/1200, '#A4DDED'],   # 25% of the range
    #     [1/600, '#76ABDF'],    # 50% of the range
    #     [1/300, '#4B9CD3'],    # 75% of the range
    #     [1/100, '#2774AE'],    # Upper values (dark blue)
    #     [1/50, '#1D428A'],     # Extra stop
    #     [1, '#00356B']         # Extra stop
    # ]

#all blue where light is very not visible
    # color_scale_stops = [
    #     [0/1000000, '#F0F8FF'],   # Lower values (light blue)
    #     [1/100000, '#B9D9EB'],    # 1% of the range
    #     [1/10000, '#ADD8E6'],     # 25% of the range
    #     [1/7000, '#A4DDED'],      # 50% of the range
    #     [1/5000, '#76ABDF'],      # 75% of the range
    #     [1/1000, '#2774AE'],      # Upper values (dark blue)
    #     [1/100, '#1D428A'],       # Extra stop
    #     [1, '#00356B']            # Extra stop
    # ]
#with purple
    # Define color scale stops
    # color_scale_stops = [
    #     [0/4789, '#B9D9EB'],     # Lower values (Light blue)
    #     [1/4789, '#D8BFD8'],     # 1% of the range (Thistle)
    #     [25/4789, '#6495ED'],    # 25% of the range (Cornflower blue)
    #     [50/4789, '#483D8B'],    # 50% of the range (Dark slate blue)
    #     [75/4789, '#6A5ACD'],    # 75% of the range (Slate blue)
    #     [100/4789, '#4B0082'],   # Upper values (Indigo)
    #     [100/4789, '#662d91'],   # Additional stop (Roku Purple)
    #     [1, '#452c63']           # Additional stop (Deep purple)
    # ]
#red to green
    color_scale_stops = [
        [0/4789, '#008000'],      # Lower values (Regular green)
        [1/4789, '#90EE90'],      # 1% of the range (Light green)
        [25/4789, '#FFFFFF'],     # 25% of the range (White)
        [50/4789, '#FF69B4'],     # 50% of the range (Hot pink)
        [75/4789, '#DC143C'],     # 75% of the range (Red)
        [100/4789, '#DC143C'],    # Upper values (Red)
        [100/4789, '#DC143C'],    # Additional stop (Red)
        [1, '#8B0000']            # Additional stop (Red)
    ]

    # Define color scale stops with shades of orange
    color_scale_stops2 = [
        [0/100, '#FFA07A'],  # LightSalmon
        [1/80, '#FF7F50'],   # Coral
        [1/6, '#FF6347'],    # Tomato
        [1/3, '#FF4500'],    # OrangeRed
        [1/2, '#FF8C00'],    # DarkOrange
        [1, '#FFA500']       # Orange
    ]
#-----------------------------------------MAIN DATA-----------------------------------------
    fig = px.scatter_mapbox(df, lat="Latitude", lon="Longitude", size_max=10,
                        color="Count",  # Set color to Count with specified color scale
                        color_continuous_scale=color_scale_stops,  # Use specified color scale
                        zoom=10, center={"lat": 40.70, "lon": -73.935242},
                        hover_data={"Latitude": True, "Longitude": True, "VIOLATION_CODE": True, 
                                    "NTAName": True, "CityCouncilDistrict": True, "CommunityDistrict": True, "Count":True},
                        custom_data=["Latitude", "Longitude", "VIOLATION_CODE", 
                                     "NTAName", "CityCouncilDistrict", "CommunityDistrict", "Count"])

    fig.update_traces(hovertemplate=
        '<b>Latitude</b>: %{customdata[0]}<br>' +
        '<b>Longitude</b>: %{customdata[1]}<br>' +
        '<b>Violation Code</b>: %{customdata[2]}<br>' +
        '<b>NTA Name</b>: %{customdata[3]}<br>' +
        '<b>City Council District</b>: %{customdata[4]}<br>' +
        '<b>Community District</b>: %{customdata[5]}<br>'+
        '<b>Count</b>: %{customdata[6]}<br>'
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        title_text="Title",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=1000,
        coloraxis_colorbar=dict(
            x=-0,   # Adjust the position of the color bar to be below the map
            y=0,
            len=0.05,  # Set the length of the color bar to be minimal
            thickness=1,  # Set the thickness of the color bar
            bgcolor='rgba(0, 0, 0, 0)',  # Make the background slightly transparent
            tickfont=dict(size=1),  # Set the font size of color bar ticks
            title_font=dict(size=1)  # Set the font size of color bar title
        )
    )

    cursor.execute(count_query, params)
    total_records = cursor.fetchone()[0]

    #-----------------------------------------PIE CHART-----------------------------------------
    pie_data = df.groupby('VIOLATION_CODE').size().reset_index(name='count')
    
    # Fetch violation code descriptions from the API and update the names in pie_data
    api_url = "https://data.cityofnewyork.us/resource/ncbg-6agr.json"
    for index, row in pie_data.iterrows():
        violation_code = row['VIOLATION_CODE']
        response = requests.get(f"{api_url}?code={violation_code}")
        data = response.json()
        if data:
            description = data[0].get('definition', f'Description for code {violation_code} not available.')
            pie_data.at[index, 'VIOLATION_CODE'] = description
        else:
            pie_data.at[index, 'VIOLATION_CODE'] = f'Description for code {violation_code} not available.'
    
    # Create the pie chart
    fig_pie = px.pie(pie_data, values='count', names='VIOLATION_CODE', color_discrete_sequence=px.colors.sequential.Oranges)
    
    # Update the layout
    fig_pie.update_layout(
        title=None,           # Remove title
        annotations=[],       # Remove annotations
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=275,
        legend=dict(
            orientation="v",   # Set orientation to vertical
            x=0.5,              # Center the legend horizontally
            xanchor="center",   # Anchor the legend to the center
            yanchor="top",      # Anchor the legend to the top
            y=-0.1,              # Position the legend just below the plot
            font=dict(size=10)  # Set the font size for the legend
        )
    )

    # Convert the pie chart to HTML
    pie_div = fig_pie.to_html(full_html=False)
    #-----------------------------------------PARKING METERS LAYER-----------------------------------------
    if 'fetch_api_data' in request.GET:
        # Check if the value of fetch_api_data is 'true'
        if request.GET['fetch_api_data'] == 'true':
            # Your API key
            api_key = 'rb3K69EGKPTJjnxxGPHqObiM1'
            
            # Create a Socrata client
            client = Socrata("data.cityofnewyork.us", api_key)
            
            # Fetch data from the API using sodapy
            results = client.get("693u-uax6", limit=50000)  # Adjust the limit as needed to fetch all records
            api_df = pd.DataFrame.from_records(results)

            # Extract latitude and longitude as float values
            api_df['lat'] = api_df['lat'].astype(float)
            api_df['long'] = api_df['long'].astype(float)

            # Drop rows with missing latitude or longitude
            api_df = api_df.dropna(subset=['lat', 'long'])

            # Print the number of records read in
            num_records = len(api_df)
            print(f"Number of records read in: {num_records}")

            # Plot API data on the map
            api_trace = px.scatter_mapbox(api_df, lat="lat", lon="long", color_discrete_sequence=['#000000']).data[0]
            #'#9e1b32'

            # Update hovertemplate for the API trace
            api_trace.hovertemplate = (
                '<b>Latitude</b>: %{lat:.2f}<br>' +
                '<b>Longitude</b>: %{lon:.2f}<br>' 
            )

            fig.add_trace(api_trace)
#-----------------------------------------RUNTIME-----------------------------------------
    end_time = time.time()  # End measuring time
    run_time = end_time - start_time  # Calculate run time
    print("Run time:", run_time, "seconds")  # Print run time to server console

    return render(request, 'plotly.html', {'plot_div': fig.to_html(full_html=False),  
                                            'pie_div': pie_div,
                                            'available_violation_codes': available_violation_codes,
                                            'available_boroughs': zip(available_boroughs, all_boroughs_result),  
                                            'boroughNames': borough_names,
                                            'total_records': total_records,
                                            'violation_code_mapping': violation_code_mapping})

























































def testing_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    violation_codes = request.GET.getlist('violation_code')  # Get a list of selected violation codes
    boroughs = request.GET.getlist('borough')  # Get a list of selected boroughs
    start_time = time.time()
    #-----------------------------------------DATABASE CONNECTION-----------------------------------------
    conn = pyodbc.connect('Driver={sql server};'
                          'Server=dotazdevsqlee04;'
                          'Database=STARS;'
                          'Trusted_Connection=yes;'
                          )
    #-----------------------------------------QUERIES-----------------------------------------
    query = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY Latitude, Longitude) AS Row_Num,
            Latitude, 
            Longitude, 
            VIOLATION_CODE,
            NTAName,
            CityCouncilDistrict,
            CommunityDistrict,
            Boro,
            COUNT(*) AS Count
        FROM [STARSParkingViolations]
        WHERE Latitude IS NOT NULL AND Longitude IS NOT NULL
    """
    borough_names = {
        'Q': 'Queens',
        'B': 'Brooklyn',
        'SI': 'Staten Island',
        'BX': 'Bronx',
        'M': 'Manhattan'
    }

    cursor = conn.cursor()
    count_query = "SELECT COUNT(*) FROM STARSParkingViolations"
    where_clauses = []
    params = []

    # Add conditions for start and end dates if they are provided
    if start_date and end_date:
        query += f" AND ISSUE_DATE BETWEEN '{start_date}' AND '{end_date}'"
        where_clauses.append("ISSUE_DATE BETWEEN ? AND ?")
        params.extend([start_date, end_date])
    # Add condition to filter out null values for latitude and longitude
    where_clauses.append("Latitude IS NOT NULL AND Longitude IS NOT NULL")

    # Add conditions for violation codes if they are provided
    if violation_codes:
        violation_codes_str = "', '".join(violation_codes)  # Join selected violation codes into a string
        query += f" AND VIOLATION_CODE IN ('{violation_codes_str}')"
        where_clauses.append("VIOLATION_CODE IN (" + ",".join(["?"] * len(violation_codes)) + ")")
        params.extend(violation_codes)
    
    # Add conditions for boroughs if they are provided
    if boroughs:
        boroughs_str = "', '".join(boroughs)  # Join selected boroughs into a string
        query += f" AND Boro IN ('{boroughs_str}')"
        where_clauses.append("Boro IN (" + ",".join(["?"] * len(boroughs)) + ")")
        params.extend(boroughs)
    
    # Construct the final SQL query
    if where_clauses:
        count_query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY Latitude, Longitude, VIOLATION_CODE, Boro, NTAName, CityCouncilDistrict, CommunityDistrict"
    
    # Execute the query and read results into a DataFrame
    df = pd.read_sql_query(query, conn)

    # Sort the DataFrame by count in ascending order
    df = df.sort_values(by='Count', ascending=True)
    #-----------------------------------------GET YEARS-----------------------------------------
    min_year = 2015
    max_year = 2024
    available_years = list(range(min_year, max_year + 1))
    date_range_str = f"{start_date} to {end_date}" if start_date and end_date else "No date range specified"
    
    # Extract unique violation codes from the DataFrame
    # Extract all unique violation codes from the database
    all_violation_codes_query = "SELECT DISTINCT VIOLATION_CODE FROM STARSParkingViolations"
    all_violation_codes_cursor = conn.cursor()
    all_violation_codes_cursor.execute(all_violation_codes_query)
    all_violation_codes_result = all_violation_codes_cursor.fetchall()
    available_violation_codes = sorted([code[0] for code in all_violation_codes_result])
    
    all_boroughs_query = "SELECT DISTINCT Boro FROM STARSParkingViolations"
    all_boroughs_cursor = conn.cursor()
    all_boroughs_cursor.execute(all_boroughs_query)
    all_boroughs_result = all_boroughs_cursor.fetchall()
    available_boroughs = [borough_names.get(borough[0], borough[0]) for borough in all_boroughs_result]


    # Extract selected boroughs from the request
    selected_boroughs = request.GET.getlist('borough')

    # Filter out None values and then sort
    available_boroughs = sorted([borough[0] for borough in all_boroughs_result if borough[0] is not None])

    # Include selected boroughs in the SQL query
    if selected_boroughs:
        boroughs_str = "', '".join(selected_boroughs)
        query += f" AND Boro IN ('{boroughs_str}')"

    #-----------------------------------------COLORS-----------------------------------------
    # Define color scale stops
    color_scale_stops = [
        [0/4789, '#B9D9EB'],   # Lower values (light blue)
        [1/2400, '#ADD8E6'],   # 1% of the range
        [1/1200, '#A4DDED'],   # 25% of the range
        [1/600, '#76ABDF'],    # 50% of the range
        [1/300, '#4B9CD3'],    # 75% of the range
        [1/100, '#2774AE'],    # Upper values (dark blue)
        [1/50, '#1D428A'],     # Extra stop
        [1, '#00356B']         # Extra stop
    ]

#all blue where light is very not visible
    # color_scale_stops = [
    #     [0/1000000, '#F0F8FF'],   # Lower values (light blue)
    #     [1/100000, '#B9D9EB'],    # 1% of the range
    #     [1/10000, '#ADD8E6'],     # 25% of the range
    #     [1/7000, '#A4DDED'],      # 50% of the range
    #     [1/5000, '#76ABDF'],      # 75% of the range
    #     [1/1000, '#2774AE'],      # Upper values (dark blue)
    #     [1/100, '#1D428A'],       # Extra stop
    #     [1, '#00356B']            # Extra stop
    # ]
#with purple
    # Define color scale stops
    # color_scale_stops = [
    #     [0/4789, '#B9D9EB'],    # Lower values
    #     [1/4789, '#ADD8E6'],    # 1% of the range
    #     [25/4789, '#6495ED'],   # 25% of the range
    #     [50/4789, '#2a52be'],   # 50% of the range
    #     [75/4789, '#00308F'],   # 75% of the range
    #     [100/4789, '#002D62'],  # Upper values
    #     [100/4789, '#662d91'],  # Additional stop
    #     [1, '#452c63']          # Additional stop
    # ]


    # Define color scale stops with shades of orange
    color_scale_stops2 = [
        [0/100, '#FFA07A'],  # LightSalmon
        [1/80, '#FF7F50'],   # Coral
        [1/6, '#FF6347'],    # Tomato
        [1/3, '#FF4500'],    # OrangeRed
        [1/2, '#FF8C00'],    # DarkOrange
        [1, '#FFA500']       # Orange
    ]
#-----------------------------------------MAIN DATA-----------------------------------------
    fig = px.scatter_mapbox(df, lat="Latitude", lon="Longitude", size_max=10,
                        color="Count", color_continuous_scale=color_scale_stops,
                        zoom=10, center={"lat": 40.730610, "lon":  -73.935242},
                        hover_data={"Latitude": True, "Longitude": True, "VIOLATION_CODE": True, 
                                    "NTAName": True, "CityCouncilDistrict": True, "CommunityDistrict": True, "Count":True},
                        custom_data=["Latitude", "Longitude", "VIOLATION_CODE", 
                                     "NTAName", "CityCouncilDistrict", "CommunityDistrict", "Count"])

    fig.update_traces(hovertemplate=
        '<b>Latitude</b>: %{customdata[0]}<br>' +
        '<b>Longitude</b>: %{customdata[1]}<br>' +
        '<b>Violation Code</b>: %{customdata[2]}<br>' +
        '<b>NTA Name</b>: %{customdata[3]}<br>' +
        '<b>City Council District</b>: %{customdata[4]}<br>' +
        '<b>Community District</b>: %{customdata[5]}<br>'+
        '<b>Count</b>: %{customdata[6]}<br>'
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        title_text="Title",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=900,
        coloraxis_colorbar=dict(
            x=0,  # Set the position of the color bar to the left
            bgcolor='rgba(255, 255, 255, 0.8)'
        )
    )
    cursor.execute(count_query, params)
    total_records = cursor.fetchone()[0]
    #-----------------------------------------PIE CHART-----------------------------------------
    pie_data = df.groupby('VIOLATION_CODE').size().reset_index(name='count')
    
    # Fetch violation code descriptions from the API and update the names in pie_data
    api_url = "https://data.cityofnewyork.us/resource/ncbg-6agr.json"
    for index, row in pie_data.iterrows():
        violation_code = row['VIOLATION_CODE']
        response = requests.get(f"{api_url}?code={violation_code}")
        data = response.json()
        if data:
            description = data[0].get('definition', f'Description for code {violation_code} not available.')
            pie_data.at[index, 'VIOLATION_CODE'] = description
        else:
            pie_data.at[index, 'VIOLATION_CODE'] = f'Description for code {violation_code} not available.'
    
    # Create the pie chart
    fig_pie = px.pie(pie_data, values='count', names='VIOLATION_CODE', color_discrete_sequence=px.colors.sequential.Oranges)
    
    # Update the layout
    fig_pie.update_layout(
        title=None,           # Remove title
        annotations=[],       # Remove annotations
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=275,
        legend=dict(
            orientation="v",   # Set orientation to vertical
            x=0.5,              # Center the legend horizontally
            xanchor="center",   # Anchor the legend to the center
            yanchor="top",      # Anchor the legend to the top
            y=-0.1,              # Position the legend just below the plot
            font=dict(size=10)  # Set the font size for the legend
        )
    )

    # Convert the pie chart to HTML
    pie_div = fig_pie.to_html(full_html=False)
    #-----------------------------------------PARKING METERS LAYER-----------------------------------------
    if 'fetch_api_data' in request.GET:
        # Check if the value of fetch_api_data is 'true'
        if request.GET['fetch_api_data'] == 'true':
            # Fetch data from the API
            api_url = "https://data.cityofnewyork.us/resource/693u-uax6.json"
            response = requests.get(api_url)
            api_data = response.json()

            # Convert API data to DataFrame
            api_df = pd.DataFrame(api_data)

            # Extract latitude and longitude as float values
            api_df['lat'] = api_df['lat'].astype(float)
            api_df['long'] = api_df['long'].astype(float)

            # Drop rows with missing latitude or longitude
            api_df = api_df.dropna(subset=['lat', 'long'])

            # Plot API data on the map
            api_trace = px.scatter_mapbox(api_df, lat="lat", lon="long", color_discrete_sequence=['#9e1b32']).data[0]

            # Update hovertemplate for the API trace
            api_trace.hovertemplate = (
                '<b>Latitude</b>: %{lat:.2f}<br>' +
                '<b>Longitude</b>: %{lon:.2f}<br>' 
            )

            fig.add_trace(api_trace)
#-----------------------------------------RUNTIME-----------------------------------------
    end_time = time.time()  # End measuring time
    run_time = end_time - start_time  # Calculate run time
    print("Run time:", run_time, "seconds")  # Print run time to server console

    return render(request, 'testing.html', {'plot_div': fig.to_html(full_html=False),  
                                            'pie_div': pie_div,
                                            'available_violation_codes': available_violation_codes,
                                            'available_boroughs': zip(available_boroughs, all_boroughs_result),  
                                            'boroughNames': borough_names,
                                            'total_records': total_records})
