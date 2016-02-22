__author__ = 'kdenny'

import geojson
from pprint import pprint

def readLocs():
    import csv
    locations = {}
    floc = "C:/Users/kdenny/Documents/AmtrakStatus/Locations.csv"
    with open(floc, 'rU') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            locdict = {}
            locdict['latitude'] = row['NORTHING']
            locdict['longitude'] = row['EASTING']
            locations[row['ARROW_CODE']] = locdict

    return locations


def createMultiLine(links,locs,trainnum):
    import json
    jsonf = "C:/Users/kdenny/Documents/AmtrakStatus/LineTest{0}.geojson".format(trainnum)
    feature_collect = []
    with open(jsonf, 'w') as outfile:
        linksjson = {}
        megadump = ""
        for link in links:
            nodelist = links[link]
            coords = []
            for node in nodelist:
                coords.append((float(locs[node]['longitude']), float(locs[node]['latitude'])))
            linefile = geojson.LineString(coords)
            linefeature = geojson.Feature(geometry=linefile, properties={'id' : link})
            feature_collect.append(linefeature)
            dumpr = geojson.dumps(linefile, sort_keys=True)
            # megadump += str(dumpr)
            linksjson[link] = dumpr
        fc = geojson.FeatureCollection(feature_collect)
        geojson.dump(fc, outfile)



    pprint(linksjson)







