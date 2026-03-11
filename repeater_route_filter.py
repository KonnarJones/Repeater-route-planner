#!/usr/bin/env python3

import argparse
import csv
import html
import math
import re
import sys
import xml.etree.ElementTree as ET


EARTH_RADIUS_M = 6371008.8
METERS_PER_MILE = 1609.344


def strip_ns(tag):
    return tag.split("}")[-1]


def normalize_text(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_freq(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = s.replace("mhz", "")
    s = s.replace(" ", "")
    return s


def haversine_m(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def latlon_to_local_xy_m(lat, lon, lat0, lon0):
    lat_rad = math.radians(lat)
    lat0_rad = math.radians(lat0)
    lon_rad = math.radians(lon)
    lon0_rad = math.radians(lon0)

    x = (lon_rad - lon0_rad) * math.cos((lat_rad + lat0_rad) / 2.0) * EARTH_RADIUS_M
    y = (lat_rad - lat0_rad) * EARTH_RADIUS_M
    return x, y


def point_to_segment_distance_and_t(px, py, ax, ay, bx, by):
    abx = bx - ax
    aby = by - ay
    apx = px - ax
    apy = py - ay

    ab_len2 = abx * abx + aby * aby

    if ab_len2 == 0:
        dx = px - ax
        dy = py - ay
        return math.hypot(dx, dy), 0.0

    t = (apx * abx + apy * aby) / ab_len2
    t = max(0.0, min(1.0, t))

    proj_x = ax + t * abx
    proj_y = ay + t * aby

    dx = px - proj_x
    dy = py - proj_y

    return math.hypot(dx, dy), t


def parse_route_kml(route_kml_path):
    tree = ET.parse(route_kml_path)
    root = tree.getroot()

    for elem in root.iter():
        if strip_ns(elem.tag) == "LineString":
            for child in elem:
                if strip_ns(child.tag) == "coordinates":
                    coords = []
                    for chunk in (child.text or "").strip().split():
                        parts = chunk.split(",")
                        if len(parts) >= 2:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            coords.append((lat, lon))
                    if len(coords) >= 2:
                        return coords

    return []


def build_route_segments(route_coords):
    lat0, lon0 = route_coords[0]

    segments = []
    cumulative_m = 0.0

    for i in range(len(route_coords) - 1):
        lat1, lon1 = route_coords[i]
        lat2, lon2 = route_coords[i + 1]

        ax, ay = latlon_to_local_xy_m(lat1, lon1, lat0, lon0)
        bx, by = latlon_to_local_xy_m(lat2, lon2, lat0, lon0)

        seg_len_m = haversine_m(lat1, lon1, lat2, lon2)

        segments.append({
            "ax": ax,
            "ay": ay,
            "bx": bx,
            "by": by,
            "seg_len_m": seg_len_m,
            "cum_start_m": cumulative_m,
        })

        cumulative_m += seg_len_m

    return segments, lat0, lon0


def compute_route_metrics(lat, lon, segments, lat0, lon0):
    px, py = latlon_to_local_xy_m(lat, lon, lat0, lon0)

    best_distance_m = None
    best_progress_m = 0.0

    for seg in segments:
        dist_m, t = point_to_segment_distance_and_t(
            px, py,
            seg["ax"], seg["ay"],
            seg["bx"], seg["by"]
        )

        progress_m = seg["cum_start_m"] + t * seg["seg_len_m"]

        if best_distance_m is None or dist_m < best_distance_m:
            best_distance_m = dist_m
            best_progress_m = progress_m

    return best_distance_m, best_progress_m


def parse_description_lines(desc_text):
    """
    Converts a KML description like:
      Kansas City<br>
      442.550000+ <br>
      On-air: Yes<br>
    into clean text lines.
    """
    if desc_text is None:
        return []

    txt = html.unescape(desc_text)
    txt = txt.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    lines = [line.strip() for line in txt.splitlines()]
    lines = [line for line in lines if line]
    return lines


def parse_freq_from_description_line(line):
    """
    Extract leading frequency from a line like:
      442.550000+
      442.675000+ 127.3
      146.940000- 110.9
    """
    if not line:
        return ""

    m = re.search(r"(\d{3}\.\d+)", line)
    if m:
        return m.group(1)
    return ""


def parse_repeater_kml(repeaters_kml_path):
    tree = ET.parse(repeaters_kml_path)
    root = tree.getroot()

    repeaters = []

    for placemark in root.iter():
        if strip_ns(placemark.tag) != "Placemark":
            continue

        name = ""
        description = ""

        for elem in placemark:
            if strip_ns(elem.tag) == "name":
                name = (elem.text or "").strip()
            elif strip_ns(elem.tag) == "description":
                description = elem.text or ""

        point = None
        for elem in placemark.iter():
            if strip_ns(elem.tag) == "Point":
                for child in elem:
                    if strip_ns(child.tag) == "coordinates":
                        parts = (child.text or "").strip().split(",")
                        if len(parts) >= 2:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            point = (lat, lon)
                            break
                if point:
                    break

        if not point:
            continue

        lines = parse_description_lines(description)

        location = lines[0] if len(lines) > 0 else ""
        freq_line = lines[1] if len(lines) > 1 else ""
        on_air_line = lines[2] if len(lines) > 2 else ""

        output_freq = parse_freq_from_description_line(freq_line)
        on_air = "yes" if "on-air: yes" in on_air_line.lower() else "no"

        lat, lon = point
        repeaters.append({
            "call": name,
            "location_from_kml": location,
            "output_freq_from_kml": output_freq,
            "on_air": on_air,
            "lat": lat,
            "lon": lon,
        })

    return repeaters


def load_csv_info(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        headers = reader.fieldnames or []

    print("\nCSV HEADERS FOUND:")
    for h in headers:
        print(f"  {h}")

    lookup = {}

    for row in rows:
        call = row.get("Call", "")
        output_freq = row.get("Output Freq", "")
        location = row.get("Location", "")

        key1 = (
            normalize_text(call),
            normalize_freq(output_freq),
            normalize_text(location),
        )

        key2 = (
            normalize_text(call),
            normalize_freq(output_freq),
        )

        lookup[key1] = row
        lookup[key2] = row

    return lookup, rows


def match_kml_to_csv(kml_repeaters, csv_lookup):
    matched = []
    unmatched_examples = []

    for rpt in kml_repeaters:
        if rpt["on_air"] == "no":
            continue

        key_with_location = (
            normalize_text(rpt["call"]),
            normalize_freq(rpt["output_freq_from_kml"]),
            normalize_text(rpt["location_from_kml"]),
        )

        key_without_location = (
            normalize_text(rpt["call"]),
            normalize_freq(rpt["output_freq_from_kml"]),
        )

        row = csv_lookup.get(key_with_location)
        if row is None:
            row = csv_lookup.get(key_without_location)

        if row is None:
            if len(unmatched_examples) < 10:
                unmatched_examples.append({
                    "call": rpt["call"],
                    "output_freq_from_kml": rpt["output_freq_from_kml"],
                    "location_from_kml": rpt["location_from_kml"],
                })
            continue

        merged = {
            "lat": rpt["lat"],
            "lon": rpt["lon"],
            "call": row.get("Call", rpt["call"]),
            "output_freq": row.get("Output Freq", rpt["output_freq_from_kml"]),
            "input_freq": row.get("Input Freq", ""),
            "uplink_tone": row.get("Uplink Tone", ""),
            "downlink_tone": row.get("Downlink Tone", ""),
            "modes": row.get("Modes", ""),
            "location": row.get("Location", rpt["location_from_kml"]),
        }

        matched.append(merged)

    print(f"\nKML repeaters loaded: {len(kml_repeaters)}")
    print(f"Matched KML repeaters to CSV rows: {len(matched)}")

    if unmatched_examples:
        print("\nSample unmatched KML repeaters:")
        for item in unmatched_examples:
            print(item)

    return matched


def main():
    parser = argparse.ArgumentParser(
        description="Filter repeaters within X miles of a route using repeater KML coordinates and CSV info."
    )
    parser.add_argument("--route-kml", required=True, help="Route KML containing a LineString")
    parser.add_argument("--repeaters-kml", required=True, help="Master repeater KML containing repeater points")
    parser.add_argument("--info-csv", required=True, help="Master repeater CSV")
    parser.add_argument("--radius-miles", required=True, type=float, help="Distance from route in miles")
    parser.add_argument("--output-csv", required=True, help="Output CSV path")

    args = parser.parse_args()

    route = parse_route_kml(args.route_kml)
    if len(route) < 2:
        print("ERROR: No valid LineString route found in route KML.", file=sys.stderr)
        sys.exit(1)

    print(f"\nRoute points loaded: {len(route)}")
    print(f"First route point: {route[0]}")
    print(f"Last route point:  {route[-1]}")

    kml_repeaters = parse_repeater_kml(args.repeaters_kml)
    csv_lookup, csv_rows = load_csv_info(args.info_csv)
    repeaters = match_kml_to_csv(kml_repeaters, csv_lookup)

    segments, lat0, lon0 = build_route_segments(route)

    radius_m = args.radius_miles * METERS_PER_MILE
    results = []

    for rpt in repeaters:
        dist_m, progress_m = compute_route_metrics(
            rpt["lat"], rpt["lon"], segments, lat0, lon0
        )

        if dist_m <= radius_m:
            results.append({
                "route_progress": round(progress_m / METERS_PER_MILE, 2),
                "callsign": rpt["call"],
                "distance_to_route": round(dist_m / METERS_PER_MILE, 2),
                "output_freq": rpt["output_freq"],
                "input_freq": rpt["input_freq"],
                "uplink_tone": rpt["uplink_tone"],
                "downlink_tone": rpt["downlink_tone"],
                "modes": rpt["modes"],
                "location": rpt["location"],
            })

    results.sort(key=lambda x: (x["route_progress"], x["distance_to_route"]))

    fieldnames = [
        "route_progress",
        "callsign",
        "distance_to_route",
        "output_freq",
        "input_freq",
        "uplink_tone",
        "downlink_tone",
        "modes",
        "location",
    ]

    with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    if results:
        print(f"\nWrote {len(results)} repeaters to {args.output_csv}")
    else:
        print("\nNo repeaters matched the route/radius/filter settings.")
        print(f"An empty CSV was still created at {args.output_csv}")


if __name__ == "__main__":
    main()