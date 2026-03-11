# Repeater Route Planner

A Python tool for finding amateur radio repeaters along a travel route.

This tool takes repeater data exported from **RepeaterBook**, a **route KML file from Google Earth**, and generates a list of repeaters located within a specified distance of the route.

It can also export those repeaters back into a **KML file for visualization in Google Earth Pro**.

---

# Features

• Merge repeater datasets from multiple states  
• Filter repeaters within X miles of a route  
• Sort repeaters in driving order along the route  
• Export results to CSV for Excel printing  
• Export repeaters as a KML file for Google Earth Pro  

---

# Example Use Case

Planning a road trip and want to know which repeaters you can hit along the way.

This tool will produce a list like:

| Route Progress | Callsign | Distance to Route | Output | Input | Tone | Location |
|---|---|---|---|---|---|---|
| 12.5 mi | WB0YRG | 1.2 mi | 442.550 | 447.550 | 127.3 | Kansas City |

You can then:

• Print the CSV for your vehicle  
• Load the KML in Google Earth  
• Pre-program repeaters into your radio  

---

# Requirements

Python 3.8+

No external dependencies required.

---

# Installation

Clone the repository:

---

# Setup and Usage

This tool works in four stages:

1. Download repeater datasets from RepeaterBook
2. Merge the datasets into master files
3. Filter repeaters along a route
4. Export the filtered repeaters as a KML map

---

# Step 1 — Download Repeater Data

Visit:

https://www.repeaterbook.com

Download both CSV and KML exports for each state and band you want to include.

Typical files will look like:

MO_2m.csv
MO_2m.kml

Place the files into the project directories:

source_data/
   csv/
   kml/

Example:

source_data/csv/MO_2m.csv
source_data/kml/MO_2m.kml

---

# Step 2 — Merge Repeater Data

Run the merge script to combine all repeater datasets into a single master dataset.

python merge_repeaters.py

This will produce:

data/all_repeaters.csv
data/all_repeaters.kml

These files contain all repeaters from every dataset and will be used by the route filter.

You normally only need to run this when adding new state datasets.

---

# Step 3 — Create a Route

Create a route in Google Earth Pro.

1. Click Add → Path
2. Draw your route
3. Right-click the path
4. Save it as:

routes/my_trip.kml

The route must contain a LineString path.

---

# Step 4 — Find Repeaters Along the Route

Run the route filter script:

python repeater_route_filter.py --route-kml routes/my_trip.kml --repeaters-kml data/all_repeaters.kml --info-csv data/all_repeaters.csv --radius-miles 20 --output-csv output/trip_repeaters.csv

Arguments:

--route-kml
KML file containing your route

--repeaters-kml
Master repeater KML file

--info-csv
Master repeater CSV file

--radius-miles
Maximum distance from the route

--output-csv
Output repeater list

Example output:

Original route points loaded: 37643
Downsampled route points used: 1882
KML repeaters loaded: 4058
Matched KML repeaters to CSV rows: 3628

Wrote 184 repeaters to output/trip_repeaters.csv

The resulting CSV can be opened in Excel for printing.

Columns include:

route_progress
callsign
distance_to_route
output_freq
input_freq
uplink_tone
downlink_tone
modes
location

---

# Step 5 — Generate a Google Earth Map

To visualize the repeaters along your route, convert the CSV results into a KML file.

Run:

python csv_to_kml.py --trip-csv output/trip_repeaters.csv --repeaters-kml data/all_repeaters.kml --output-kml output/trip_repeaters.kml

Arguments:

--trip-csv
Filtered repeater CSV from previous step

--repeaters-kml
Master repeater KML

--output-kml
Generated KML file

---

# Step 6 — Open in Google Earth

Open the generated file:

output/trip_repeaters.kml

in Google Earth Pro.

Each repeater will appear as a placemark showing:

Route Progress
Distance to Route
Output Frequency
Input Frequency
Uplink Tone
Downlink Tone
Modes
Location

This allows quick visual inspection of repeaters along your travel route.

---

# Typical Workflow

Download repeater datasets
        ↓
Place CSV + KML files into source_data/
        ↓
Run merge_repeaters.py
        ↓
Create a route in Google Earth
        ↓
Run repeater_route_filter.py
        ↓
Open CSV in Excel
        ↓
Generate KML map
        ↓
Open results in Google Earth

---
