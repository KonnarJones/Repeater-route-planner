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
