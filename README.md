# NYC Parking Violations Interactive Map (Plotly)
An interactive map visualizing NYC parking violations from 2015 to the present using Plotly, with dynamic filtering and intuitive data exploration tools.

**Tech Stack**
- JavaScript
- Plotly
- HTML / CSS
- Django
- Backend API (NYC OpenData)

**Key Features**
- Interactive map displaying parking violation density by location (redder = more violations).
- Dynamic sidebar with:
  - About section explaining the map’s purpose.
  - Pie chart showing violation ratios within the selected range, downloadable via Plotly.
- Legend correlating colors to violation types.
- Dynamic title reflecting the current year range displayed.
- Total record count that updates based on filters (borough & violation code).
- Start and end year dropdowns for filtering data.
- Borough and violation code filters affecting both map and pie chart.
- Layer toggle buttons (currently includes a Parking Meters layer via NYC OpenData).
- Loading indicator during data refresh.
- Hover tooltips displaying violation counts and location details.

**Lessons Learned**
- Integrating Plotly for map-based heatmaps and interactive charts.
- Efficiently filtering large datasets client-side for performance.
- Designing intuitive user interfaces for exploring spatial and categorical data.

Areas for Improvement
- Add additional layers (e.g., street infrastructure, traffic camera data).
- Improve loading speed, as over 2 billion records are beign read in
- Enable exporting filtered data as CSV for user analysis.
- Incorporate time-based animation to visualize violation trends over years.

**Setup Instructions**
- Clone this repository:
```git clone https://github.com/cbcj3000/Parking-Violations-Plotly.git```
- Open plotly.html in your browser.

**How to Read the Data**
- Each point represents a location with at least one recorded parking violation.
- Redder spots indicate higher violation counts.
- Hover over points to view detailed counts and location info.

*Note: The dataset is filtered to 2015 onwards due to accuracy limitations in earlier data.*
