__author__ = 'kdenny'

from HTMLParser import *
import requests
from bs4 import BeautifulSoup
from pprint import pprint

def getAndParse(trainnum,nodes):

    data = []

    # link = 'http://juckins.net/amtrak_status/archive/html/history.php?train_num={0}&station=&date_start=01%2F01%2F2015&date_end=02%2F21%2F2016&df1=1&df2=1&df3=1&df4=1&df5=1&df6=1&df7=1&sort=schDp&sort_dir=DESC&co=gt&limit_mins=&dfon=1'.format(trainnum)

    link = 'http://juckins.net/amtrak_status/archive/html/history.php?train_num={0}&station=&date_start=02%2F12%2F2016&date_end=02%2F21%2F2016&df1=1&df2=1&df3=1&df4=1&df5=1&df6=1&df7=1&sort=schDp&sort_dir=DESC&co=gt&limit_mins=&dfon=1'.format(trainnum)
    result = requests.get(link)
    c = result.content

    finaldict = {}

    soup = BeautifulSoup(c)
    table = soup.table

    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        data.append([ele for ele in cols if ele]) # Get rid of empty values

    datadict = {}
    dates = set()
    for row in data:
        if len(row) > 4:
            minidict = {}
            minidict['date'] = row[0][:10]
            # print(minidict['date'])
            dates.add(minidict['date'])
            minidict['node'] = row[1]
            minidict['schedtime'] = row[2][11:19].strip()
            # print(minidict['schedtime'])
            if len(row) > 3 and (row[3][:3] != 'Arr'):
                delta = 0
                minidict['actualtime'] = row[3]
                if ":" in minidict['actualtime']:
                    hoursind = minidict['actualtime'].index(":")
                    actualhour = minidict['actualtime'][:hoursind]
                    actualmin = minidict['actualtime'][(hoursind+1):(hoursind+3)]
                else:
                    hoursind = 0
                    actualhour = 0
                    actualmin = 0

                if ":" in minidict['schedtime']:
                    hoursind2 = minidict['schedtime'].index(":")
                    schedhour = minidict['schedtime'][:hoursind2]
                    schedmin = minidict['schedtime'][(hoursind2+1):(hoursind2+3)]
                else:
                    hoursind2 = 0
                    schedhour = 0
                    schedmin = 0
                if int(actualhour) != 12 and int(schedhour) != 12 and (int(actualhour) - int(schedhour) < 8) and (int(actualhour) - int(schedhour) > -8):
                    delta = (int(actualhour) - int(schedhour)) * 60
                elif int(actualhour) == 12 and int(schedhour) != 12:
                    actualhour = 0
                    delta = (12 - int(schedhour)) * 60
                elif int(schedhour) == 12 and int(actualhour) != 12:
                    schedhour = 0
                    delta = (int(actualhour) - schedhour) * 60
                elif int(schedhour) == 12 and int(actualhour) != 0:
                    delta = 0
                elif (int(actualhour) - int(schedhour) > 8) or (int(actualhour) - int(schedhour) < -8):
                    schedhour = int(schedhour) - 12
                    delta = (int(actualhour) - int(schedhour)) * 60

                mindelta = int(actualmin) - int(schedmin)
                if mindelta < 0:
                    delta = delta + mindelta
                else:
                    delta += mindelta
                minidict['delta'] = delta
            else:
                minidict['actualtime'] = 'None'
                minidict['delta'] = "N/A"

            if str(minidict['node']) in nodes:
                stringkey = str(minidict['date']) + "," + str(minidict['node'])
                datadict[stringkey] = minidict

    pprint(datadict)

    for date in dates:
        datemovements = {}
        for key in datadict:
            if datadict[key]['date'] == date:
                datemovements[datadict[key]['node']] = datadict[key]

        finaldict[date] = datemovements


    # pprint(finaldict)

    return finaldict


def calclinkdelays(results,nodes,trainnum,direction,firstnode):
    from pprint import *
    linkdelays = {}
    links = set()
    for date in results:
        datedelays = {}
        for node in nodes:
            linkdelay = {}
            link = ""
            if node in results[date] and node != firstnode and nodes.index(node) < (len(nodes)-2):
                if direction == 'down':
                    node2 = nodes[(nodes.index(node)-1)]
                    count = nodes.index(node) - 1
                    while node2 not in results[date]:
                        count = count - 1
                        node2 = nodes[(count)]
                if direction == 'up':
                    node2 = nodes[(nodes.index(node)+1)]
                    count = nodes.index(node) + 1
                    while node2 not in results[date] and (count+1) < len(nodes):
                        print node2
                        count = count + 1
                        print len(nodes)
                        print count
                        node2 = nodes[(count)]
                if node2 != 'ALX':
                    link = "{0}-{1}".format(node2,node)
                    links.add(link)
                    linkdelay['date'] = date
                    linkdelay['trainnum'] = trainnum
                    linkdelay['link'] = link
                    linkdelay['origin'] = node2
                    if node2 in results[date]:
                        linkdelay['origindelay'] = results[date][node2]['delta']
                    elif node2 not in results[date]:
                        linkdelay['origindelay'] = "N/A"
                    linkdelay['destination'] = node
                    linkdelay['destinationdelay'] = results[date][node]['delta']
                    if linkdelay['origindelay'] != 'N/A' and linkdelay['destinationdelay'] != 'N/A':
                        linkdelay['linkdelay'] = linkdelay['origindelay'] - linkdelay['destinationdelay']
                    else:
                        linkdelay['linkdelay'] = 0
                    if linkdelay['destination'] != firstnode:
                        datedelays[link] = linkdelay
        linkdelays[date] = datedelays
    return linkdelays


def writeResults(linkdelays,outputloc,trainnum):
    import csv
    with open(outputloc, 'wb') as b:
        # fieldnames2 = ["VMLoc","Connecting Node","Track","Orig/Dest","Link"]
        resultsfields = ["trainnum","date","link","linkdelay","origin","origindelay","destination","destinationdelay"]

        writer = csv.DictWriter(b, fieldnames=resultsfields)
        writer.writeheader()

        for date in linkdelays:
            for link in linkdelays[date]:
                rowa = linkdelays[date][link]

                writer.writerow(rowa)

        b.close()

def processunusednodes(linkdelays,direction):
    usednodes = set()
    links = set()
    newlinks = {}
    for date in linkdelays:
        for link in linkdelays[date]:
            usednodes.add(linkdelays[date][link]['origin'])
            usednodes.add(linkdelays[date][link]['destination'])
            links.add(link)

    for link in links:
        node1 = link[:3]
        node2 = link[4:]
        if direction == 'up':
            newlinks[link] = [node1]
            while (nodes.index(node1) - 1) != nodes.index(node2):
                node1 = nodes[nodes.index(node1)-1]
                newlinks[link].append(node1)
            newlinks[link].append(node2)
        if direction == 'down':
            newlinks[link] = [node1]
            while (nodes.index(node1) + 1) < nodes.index(node2):
                node1 = nodes[nodes.index(node1)+1]
                newlinks[link].append(node1)
            newlinks[link].append(node2)

    return newlinks



# trainnum = '171'
# direction = 'down'
# firstnode = 'BOS'
# lastnode = 'ALX'

trainnum = '171'
direction = 'down'
firstnode = 'BOS'
lastnode = 'BOS'

nodes = ['BOS','BBY','RTE','PVD','KIN','WLY','NLC','OSB','NHV','BRP','STM','NRO','NYP','NWK','EWR','MET','NBK','PJC','TRE','PHN','PHL','WIL','NRK','ABE','BAL','BWI','NCR','WAS','ALX']



results = getAndParse(trainnum,nodes)

linkdelays = calclinkdelays(results,nodes,trainnum,direction,firstnode)

outputloc = 'C:/Users/kdenny/Documents/AmtrakStatus/{0}delaysreport.csv'.format(trainnum)

writeResults(linkdelays,outputloc,trainnum)

newlinks = processunusednodes(linkdelays,direction)

from GeoJSONtest import *

locs = readLocs()

linejson = createMultiLine(newlinks,locs,trainnum)






