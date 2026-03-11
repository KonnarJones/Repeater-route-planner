#!/usr/bin/env python3

import argparse
import csv
import html
import re
import sys
import xml.etree.ElementTree as ET


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


def parse_description_lines(desc_text):
    if desc_text is None:
        return []

    txt = html.unescape(desc_text)
    txt = txt.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    lines = [line.strip() for line in txt.splitlines()]
    lines = [line for line in lines if line]
    return lines


def parse_freq_from_description_line(line):
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
        output_freq = parse_freq_from_description_line(freq_line)

        lat, lon = point
        repeaters.append({
            "callsign": name,
            "output_freq": output_freq,
            "location": location,
            "lat": lat,
            "lon": lon,
        })

    return repeaters


def load_trip_csv(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_kml_lookup(repeaters):
    lookup = {}

    for rpt in repeaters:
        key1 = (
            normalize_text(rpt["callsign"]),
            normalize_freq(rpt["output_freq"]),
            normalize_text(rpt["location"]),
        )
        key2 = (
            normalize_text(rpt["callsign"]),
            normalize_freq(rpt["output_freq"]),
        )

        lookup[key1] = rpt
        lookup[key2] = rpt

    return lookup


def make_description(row):
    lines = [
        f"Route Progress: {row.get('route_progress', '')} mi",
        f"Distance to Route: {row.get('distance_to_route', '')} mi",
        f"Output Freq: {row.get('output_freq', '')}",
        f"Input Freq: {row.get('input_freq', '')}",
        f"Uplink Tone: {row.get('uplink_tone', '')}",
        f"Downlink Tone: {row.get('downlink_tone', '')}",
        f"Modes: {row.get('modes', '')}",
        f"Location: {row.get('location', '')}",
    ]
    return "<br>".join(lines)


def write_kml(rows, kml_lookup, output_kml):
    ns = "http://www.opengis.net/kml/2.2"
    ET.register_namespace("", ns)

    kml_root = ET.Element(f"{{{ns}}}kml")
    doc = ET.SubElement(kml_root, f"{{{ns}}}Document")

    name_el = ET.SubElement(doc, f"{{{ns}}}name")
    name_el.text = "Trip Repeaters"

    matched = 0
    unmatched = []

    for row in rows:
        key1 = (
            normalize_text(row.get("callsign", "")),
            normalize_freq(row.get("output_freq", "")),
            normalize_text(row.get("location", "")),
        )
        key2 = (
            normalize_text(row.get("callsign", "")),
            normalize_freq(row.get("output_freq", "")),
        )

        rpt = kml_lookup.get(key1)
        if rpt is None:
            rpt = kml_lookup.get(key2)

        if rpt is None:
            if len(unmatched) < 10:
                unmatched.append({
                    "callsign": row.get("callsign", ""),
                    "output_freq": row.get("output_freq", ""),
                    "location": row.get("location", ""),
                })
            continue

        placemark = ET.SubElement(doc, f"{{{ns}}}Placemark")

        name_el = ET.SubElement(placemark, f"{{{ns}}}name")
        name_el.text = row.get("callsign", "")

        desc_el = ET.SubElement(placemark, f"{{{ns}}}description")
        desc_el.text = make_description(row)

        point_el = ET.SubElement(placemark, f"{{{ns}}}Point")
        coords_el = ET.SubElement(point_el, f"{{{ns}}}coordinates")
        coords_el.text = f"{rpt['lon']},{rpt['lat']},0"

        matched += 1

    tree = ET.ElementTree(kml_root)
    tree.write(output_kml, encoding="utf-8", xml_declaration=True)

    print(f"Wrote {matched} placemarks to {output_kml}")

    if unmatched:
        print("\nSample unmatched rows:")
        for item in unmatched:
            print(item)


def main():
    parser = argparse.ArgumentParser(
        description="Convert filtered repeater CSV into a KML for Google Earth Pro."
    )
    parser.add_argument("--trip-csv", required=True, help="Filtered trip repeater CSV")
    parser.add_argument("--repeaters-kml", required=True, help="Master repeater KML")
    parser.add_argument("--output-kml", required=True, help="Output KML file")
    args = parser.parse_args()

    rows = load_trip_csv(args.trip_csv)
    if not rows:
        print("ERROR: Trip CSV has no rows.", file=sys.stderr)
        sys.exit(1)

    repeaters = parse_repeater_kml(args.repeaters_kml)
    lookup = build_kml_lookup(repeaters)

    print(f"Trip CSV rows loaded: {len(rows)}")
    print(f"Master KML repeaters loaded: {len(repeaters)}")

    write_kml(rows, lookup, args.output_kml)


if __name__ == "__main__":
    main()