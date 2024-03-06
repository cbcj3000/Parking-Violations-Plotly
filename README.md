# Parking-Violations-Plotly
This map displays parking violations recorded from the year 2015 to the present in an interactive map application using Plotly. Some functionality is described below:
- A side bar with:
  - An about section saying what the website does
  - A pie chart that shows the ratio of violataions shown in the specified range
      - Dynamic title that reminds the user of the range shown on the map
      - A pie chart sorted by color. The plotly library allows the user to download the pie chart
      - A legend that correlates the color to the violation. The Plotly library also allows users to remove and add section of the pie chart back by clicking on a specific violation code sqaure
- Total Records that says how many records are in the specified data range and is also changed by the filters(borough & violation code)
- Start and End year drop downs that filter the data when apply is clicked
- Borough Filter
- Violation Filter(this affects the pie chart)
- Layers Buttons
   - Only filter currently shown is parking meters and is retrieved fromt he backend using an API from OpenData

How to read the data: Each point represents a spot where at least one parking violation occured. The darker the spot, the more violations occured at that location. You can see more information about a spot, icluding the amount of violations when you hover over it.

INCLUDE CHRISTINA:
- PHOTO OF THE POPUPS
- GRAND PHOTO
- CHANGE RANGE
- CHANGE FILTERS
- SPECIFIC PHOTO OF THE PIE CHART ONLY

Notes:
- I set the min year to 2015 as based on the data I was using anything before 2015 is not as accurate
