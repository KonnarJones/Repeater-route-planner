#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path
from glob import glob
import xml.etree.ElementTree as ET
import copy


def merge_csv(csv_files, output_csv):

    headers = set()
    rows = []

    for f in csv_files:
        with open(f, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)

            headers.update(reader.fieldnames)

            for r in reader:
                rows.append(r)

    headers = list(headers)

    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)

    with open(output_csv, "w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(file, fieldnames=headers)

        writer.writeheader()

        for r in rows:
            writer.writerow(r)

    print(f"Merged {len(rows)} rows into {output_csv}")


def strip_ns(tag):

    return tag.split("}")[-1]


def merge_kml(kml_files, output_kml):

    ns = "http://www.opengis.net/kml/2.2"

    ET.register_namespace("", ns)

    root = ET.Element("{%s}kml" % ns)

    doc = ET.SubElement(root, "{%s}Document" % ns)

    count = 0

    for f in kml_files:

        tree = ET.parse(f)

        r = tree.getroot()

        for el in r.iter():

            if strip_ns(el.tag) == "Placemark":

                doc.append(copy.deepcopy(el))

                count += 1

    tree = ET.ElementTree(root)

    Path(output_kml).parent.mkdir(parents=True, exist_ok=True)

    tree.write(output_kml, encoding="utf-8", xml_declaration=True)

    print(f"Merged {count} placemarks into {output_kml}")


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--csv", nargs="+", required=True)

    parser.add_argument("--kml", nargs="+", required=True)

    parser.add_argument("--output-csv", required=True)

    parser.add_argument("--output-kml", required=True)

    args = parser.parse_args()

    csv_files = []

    for p in args.csv:

        csv_files.extend(glob(p))

    kml_files = []

    for p in args.kml:

        kml_files.extend(glob(p))

    merge_csv(csv_files, args.output_csv)

    merge_kml(kml_files, args.output_kml)


if __name__ == "__main__":

    main()