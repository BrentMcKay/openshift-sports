import os,sys
from html import HTML
from BeautifulSoup import BeautifulSoup

import urllib
import re

from flask import Flask, request, url_for
app = Flask(__name__)

#################################################
mlbNames = {
'WSH':'Washington Nationals','SF':'San Francisco Giants','CHW':'Chicago White Sox','MIA':'Miami Marlins','CIN':'Cincinnati Reds','PHI':'Philadelphia Phillies',
'LAD':'Los Angeles Dodgers','BOS':'Boston Red Sox','CHC':'Chicago Cubs','TB':'Tampa Bay Rays','MIL':'Milwaukee Brewers','MIN':'Minnesota Twins',
'STL':'St. Louis Cardinals','LAA':'Los Angeles Angels','CLE':'Cleveland Indians','NYY':'New York Yankees','KC':'Kansas City Royals','TEX':'Texas Rangers',
'SEA':'Seattle Mariners','DET':'Detroit Tigers','BAL':'Baltimore Orioles','OAK':'Oakland Athletics','HOU':'Houston Astros','COL':'Colorado Rockies',
'PIT':'Pittsburgh Pirates','SD':'San Diego Padres','TOR':'Toronto Blue Jays','NYM':'New York Mets','ARI':'Arizona Diamondbacks','ATL':'Atlanta Braves',
'FLA':'Florida Marlins'
}

nflNames = {
'SEA':'Seattle Seahawks','DAL':'Dallas Cowboys','MIA':'Miami Dolphins','MIN':'Minnesota Vikings','SD':'San Diego Chargers','NYG':'New York Giants','CHI':'Chicago Bears','JAX':'Jacksonville Jaguars',
'GB':'Green Bay Packers','PIT':'Pittsburgh Steelers','ARI':'Arizona Cardinals','CAR':'Carolina Panthers','HOU':'Houston Texans','SF':'San Francisco 49ers','WSH':'Washington Redskins','TEN':'Tennessee Titans',
'IND':'Indianapolis Colts','PHI':'Philadelphia Eagles','BAL':'Baltimore Ravens','KC':'Kansas City Chiefs','CIN':'Cincinnati Bengals','ATL':'Atlanta Falcons','NYJ':'New York Jets','TB':'Tampa Bay Buccaneers',
'DEN':'Denver Broncos','NE':'New England Patriots','NO':'New Orleans Saints','BUF':'Buffalo Bills','STL':'St. Louis Rams','DET':'Detroit Lions','CLE':'Cleveland Browns','OAK':'Oakland Raiders'
}

nbaNames = {
'MIA':'Miami Heat','MEM':'Memphis Grizzlies','BKN':'Brooklyn Nets','POR':'Portland Trailblazers','GS':'Golden State Warriors','ORL':'Orlando Magic',
'OKC':'Oklahoma City Thunder','BOS':'Boston Celtics','PHI':'Philadelphia 76ers','MIL':'Milwaukee Bucks','PHX':'Phoenix Suns','CHA':'Charlotte Hornets',
'DEN':'Denver Nuggets','ATL':'Atlanta Hawks','MIN':'Minnesota Timberwolves','DAL':'Dallas Mavericks','TOR':'Toronto Raptors','WSH':'Washington Wizards',
'SA':'San Antonio Spurs','IND':'Indiana Pacers','UTAH':'Utah Jazz','HOU':'Houston Rockets','CLE':'Cleveland Cavaliers','SAC':'Sacramento Kings',
'LAL':'Los Angeles Lakers','LAC':'Los Angeles Clippers','NY':'New York Knicks','CHI':'Chicago Bulls','NO':'New Orleans Hornets','DET':'Detroit Pistons'
}

#################################################
@app.route('/')
#def hello_world():
#    return 'Hello World!'
def main():
    return "Hello, World!"


#################################################
@app.route("/scores")
def scores():
    outstr = ''

    # parse args for week and year
    year = request.args.get('year','2015', type=str)
    week = request.args.get('week','1', type=str)

    #print (year, week)

    # Open ESPN scores page for year and week
    url='http://espn.go.com/nfl/scoreboard/_/year/' + year + '/seasontype/2/week/' + week
    #print (url) 
    scoresrc=urllib.urlopen(url)
    scoretext=scoresrc.read()
        
    # truncate score text after string "teamsOnBye"
    scoretext = scoretext.split('teamsOnBye', 1)[0]

    # Get team names
    teamre = re.compile('"shortDisplayName":"(\w+)"')
    teamiter = teamre.finditer(scoretext)

    # Get scores (will be in same order as teams
    scorere = re.compile('"score":"(\d+)"')
    scoreiter = scorere.finditer(scoretext)

    # Get home/away
    homeawayre = re.compile('"homeAway":"([ha])')
    homeawayiter = homeawayre.finditer(scoretext)


    try:

        while ( 1 ):
            # Take home and road teams and scores from iterators in order
            home = next(teamiter).group(1)
            road = next(teamiter).group(1)
            homescore = next(scoreiter).group(1)
            roadscore = next(scoreiter).group(1)

            # print line for each game
            outstr += home + "," + homescore + "," + road + "," + roadscore + "<br \>"

    except StopIteration:
        pass

    return outstr
    



#################################################
@app.route("/pool/nfl")
def poolnfl():

    teams = {}
    count = 99

    outstr = ""

    # parse args for league and year
    year = request.args.get('year','2015', type=str)
    league = request.args.get('league','family', type=str)

    # Open file containing owners and teams
    filename = "nfl."+league+".teams."+year
    #ownertext = open("nfl.family.teams.2015").read()
    try:
        #ownertext = open(filename).read()
        ownertext = open(os.path.join(os.path.dirname(__file__),filename),'r').read()
    except IOError:
        return filename + " not found"

    # If there are dashes in owner file, it's an auction league
    if ( ownertext.find('-') == -1 ):
        auction = False
    else:
        auction = True

    # split into lines
    lines = ownertext.split("\n")
    betPerGame = float(lines.pop(0))

    # Open ESPN standings page
    url='http://espn.go.com/nfl/standings/_/season/' + year 
    #print (url) 
    standingstext=urllib.urlopen(url)
    standings = BeautifulSoup(standingstext)

    # get all the <tr> entries
    for row in standings.findAll('tr'):

        # get all the <td> entries in current row
        for td in row.findAll('td'):

            # get all the <span> entries in this td
            spans = td.findAll('span')

            # If there are 3 or 4 spans, this is a team name.  If 4, there is a playoff key before the name
            if ( len(spans) == 3 or len(spans) == 4 ):
                abbr = spans[len(spans)-2].findAll('abbr')
                teamname = abbr[0].string
                #print teamname
                teams[teamname] = [0,0,0]
                count = 0
            else:
                # The 3 <td> entries after the <td> with the team name are w, l, and t
                if ( count < 3 ):
                    #print td.string
                    teams[teamname][count] = int(td.string)
                    count = count + 1


    # read all the owners and their teams
    ownerNames = []
    ownerTeams = {}
    ownerCost = {}
    ownerW = {}
    ownerL = {}
    ownerT = {}

    # For auction, every line in owner file is formatted as owner:team-cost:team-cost....
    # If not an auction, format is owner:team:team:...
    while ( len(lines) > 0 ):
        # pop next line from file
        ownerLine = lines.pop(0)
        # split by :
        ownerFields = ownerLine.split(":")
        # owner name is first field
        ownerName = ownerFields.pop(0)

        # Skip any empty lines
        if ( ownerName == '' ):
            continue

        ownerNames.append(ownerName)

        # Create dicts for this owner
        # List of teams owned
        ownerTeams[ownerName] = list()
        # Total owner cost
        ownerCost[ownerName] = 0
    
        # Total owner W/L/T
        ownerW[ownerName] = 0
        ownerL[ownerName] = 0
        ownerT[ownerName] = 0

        # select all the teams for this owner
        while ( len( ownerFields ) > 0 ):
            if ( auction ):
                # split out the cost and the team name
                teamCost = ownerFields.pop(0).split("-")
                team = teamCost[0]
                cost = teamCost[1]
            else:
                team = ownerFields.pop(0)
                cost = 0
            # print (team, cost)

            if ( team in teams ):
                # Add team to owner list
                ownerTeams[ownerName].append(team)

                # Add cost to owner cost
                ownerCost[ownerName] += int(cost)

                # Add cost to teams dictionary
                teams[team].append(int(cost))

                # Add team record to owner record
                ownerW[ownerName] += teams[team][0]
                ownerL[ownerName] += teams[team][1]
                ownerT[ownerName] += teams[team][2]


    #for owner in ownerTeams.keys():
        #print owner, ownerCost[owner], ownerW[owner], ownerL[owner], ownerT[owner]
        #for teamname in ownerTeams[owner]:
            #print teamname, teams[teamname][3], teams[teamname][0], teams[teamname][1], teams[team


    # Create HTML object
    h = HTML()

    # Add HTML header info
    #output = 'Content-type: text/html\n\n'
    outstr += '<HTML>\n<HEAD>\n<TITLE>' + year + ' NFL Standings</TITLE>\n<link rel="stylesheet"'
    outstr += ' type="text/css"'
    outstr += ' href="' + url_for('static', filename = 'standings.css') + '"'
    #outstr += ' href="static/standings.css"'
    outstr += '/>\n</HEAD>\n<BODY>\n'


    # Create main HTML table

    t = h.table( caption = str(year) + ' NFL pool standings')

    # Add table header
    t.th('Owner/Team')
    if ( auction ):
        t.th('Cost')
    t.th('W')
    t.th('L')
    t.th('T')


    # Iterate through the owners
    for owner in ownerNames:

        # Create row for owner name and summary
        orow = t.tr()
        orow.th(owner, align='left')
        if ( auction ):
            orow.th(str(ownerCost[owner]), align = 'right')
        orow.th(str(ownerW[owner]), align = 'right')
        orow.th(str(ownerL[owner]), align = 'right')
        orow.th(str(ownerT[owner]), align = 'right')
        orow.th("$%5.2f" % (betPerGame * (ownerW[owner] - ownerL[owner])), align = 'right')

        # Create row for each team picked by this owner
        for teamname in ownerTeams[owner]:
            trow = t.tr()
            trow.td(nflNames[teamname], klass = 'indented')
            if ( auction ):
                trow.td(str(teams[teamname][3]), align = 'right')
            trow.td(str(teams[teamname][0]), align = 'right')
            trow.td(str(teams[teamname][1]), align = 'right')
            trow.td(str(teams[teamname][2]), align = 'right')

    # Add html table to the output string
    outstr += str(t)

    # Add html closing
    outstr += '</BODY></HTML>\n'

    return outstr



#################################################

# Baseball

#################################################
@app.route("/pool/mlb")
def poolmlb():

    teams = {}
    count = 99

    outstr = ""

    # parse args for year
    year = request.args.get('year','2016', type=str)

    # Open file containing owners and teams
    filename = "mlb.teams."+year
    try:
        #ownertext = open(filename).read()
        ownertext = open(os.path.join(os.path.dirname(__file__),filename),'r').read()
    except IOError:
        return filename + " not found"

    # If there are dashes in owner file, it's an auction league
    if ( ownertext.find('-') == -1 ):
        auction = False
    else:
        auction = True

    # split into lines
    lines = ownertext.split("\n")
    betPerGame = float(lines.pop(0))

    # Open ESPN standings page
    url='http://espn.go.com/mlb/standings/_/season/' + year 
    #print (url) 
    standingstext=urllib.urlopen(url)
    standings = BeautifulSoup(standingstext)

    # get all the <tr> entries
    for row in standings.findAll('tr'):

        # get all the <td> entries in current row
        for td in row.findAll('td'):

            # get all the <span> entries in this td
            spans = td.findAll('span')

            # If there are 3 or 4 spans, this is a team name.  If 4, there is a playoff key before the name
            if ( len(spans) == 3 or len(spans) == 4 ):
                abbr = spans[len(spans)-2].findAll('abbr')
                teamname = abbr[0].string
                #print teamname
                # W L HG RS RA
                teams[teamname] = [0,0,0,0,0]
                count = 0
            else:
                # The 2 <td> entries after the <td> with the team name are W and L
                if ( count < 2 ):
                    #print td.string
                    teams[teamname][count] = int(td.string)
                # 5th td is home w-l record
                elif ( count == 4 ):
                    #print td.string
                    hg = td.string.split("-")
                    teams[teamname][2] = int(hg[0]) + int(hg[1])
                    #print teams[teamname][2]
                # 7th td is RS
                elif ( count == 6 ):
                    #print td.string
                    teams[teamname][3] = int(td.string)
                # 8th td is RS
                elif ( count == 7 ):
                    #print td.string
                    teams[teamname][4] = int(td.string)

                count = count + 1

    # read all the owners and their teams
    ownerNames = []
    ownerTeams = {}
    ownerCost = {}
    ownerW = {}
    ownerL = {}
    ownerHomeGames = {}
    ownerRS = {}
    ownerRA = {}

    # For auction, every line in owner file is formatted as owner:team-cost:team-cost....
    # If not an auction, format is owner:team:team:...
    while ( len(lines) > 0 ):
        # pop next line from file
        ownerLine = lines.pop(0)
        # split by :
        ownerFields = ownerLine.split(":")
        # owner name is first field
        ownerName = ownerFields.pop(0)

        # Skip any empty lines
        if ( ownerName == '' ):
            continue


        # Create dicts for this owner
        # List of teams owned
        ownerNames.append(ownerName)
        ownerTeams[ownerName] = list()
        # Total owner cost
        ownerCost[ownerName] = 0
    
        # Total owner W/L, HG, RS, RA
        ownerW[ownerName] = 0
        ownerL[ownerName] = 0
        ownerHomeGames[ownerName] = 0
        ownerRS[ownerName] = 0
        ownerRA[ownerName] = 0

        # select all the teams for this owner
        while ( len( ownerFields ) > 0 ):
            if ( auction ):
                # split out the cost and the team name
                teamCost = ownerFields.pop(0).split("-")
                team = teamCost[0]
                cost = teamCost[1]
            else:
                team = ownerFields.pop(0)
                cost = 0
            # print (team, cost)

            if ( team in teams ):
                # Add team to owner list
                ownerTeams[ownerName].append(team)

                # Add cost to owner cost
                ownerCost[ownerName] += int(cost)

                # Add cost to teams dictionary
                teams[team].append(int(cost))

                # Add team record to owner record
                ownerW[ownerName] += teams[team][0]
                ownerL[ownerName] += teams[team][1]
                ownerHomeGames[ownerName] += teams[team][2]
                ownerRS[ownerName] += teams[team][3]
                ownerRA[ownerName] += teams[team][4]

    # Create HTML object
    h = HTML()

    # Add HTML header info
    #output = 'Content-type: text/html\n\n'
    outstr += '<HTML>\n<HEAD>\n<TITLE>' + year + ' MLB Standings</TITLE>\n<link rel="stylesheet"'
    outstr += ' type="text/css"'
    outstr += ' href="' + url_for('static', filename = 'standings.css') + '"'
    #outstr += ' href="static/standings.css"'
    outstr += '/>\n</HEAD>\n<BODY>\n'


    # Create main HTML table

    t = h.table( caption = str(year) + ' MLB pool standings')

    # Add table header
    t.th('Owner/Team')
    if ( auction ):
        t.th('Cost')
    t.th('W')
    t.th('L')
    t.th('EW')
    t.th('EL')
    t.th('EHGR')


    # Iterate through the owners
    for owner in ownerNames:

        w = ownerW[owner]
        l = ownerL[owner]
        ehgr = w + l - ownerHomeGames[owner]*2
        rs = ownerRS[owner]
        ra = ownerRA[owner]
        if ( rs + ra > 0 ):
            epct = (rs**1.81)/(rs**1.81 + ra**1.81)
        else:
            epct = 0.0
        ew = int(epct * (w + l))
        el = w + l - ew

        # Create row for owner name and summary
        orow = t.tr()
        orow.th(owner, align='left')
        if ( auction ):
            orow.th(str(ownerCost[owner]), align = 'right')
        orow.th(str(ownerW[owner]), align = 'right')
        orow.th(str(ownerL[owner]), align = 'right')
        orow.th(str(ew), align = 'right')
        orow.th(str(el), align = 'right')
        orow.th(str(ehgr), align = 'right')
        orow.th("$%5.2f" % (betPerGame * (ownerW[owner] - ownerL[owner])), align = 'right')

        # Create row for each team picked by this owner
        for teamname in ownerTeams[owner]:
            w = teams[teamname][0]
            l = teams[teamname][1]
            ehgr = w + l - teams[teamname][2]*2
            rs = teams[teamname][3]
            ra = teams[teamname][4]
            if ( rs + ra > 0 ):
                epct = (rs**2.0)/(rs**2.0 + ra**2.0)
            else:
                epct = 0.0
            ew = int(epct * (w + l))
            el = w + l - ew

            trow = t.tr()
            trow.td(mlbNames[teamname], klass = 'indented')
            if ( auction ):
                trow.td(str(teams[teamname][5]), align = 'right')
            trow.td(str(w), align = 'right')
            trow.td(str(l), align = 'right')
            trow.td(str(ew), align = 'right')
            trow.td(str(el), align = 'right')
            trow.td(str(ehgr), align = 'right')

    # Add html table to the output string
    outstr += str(t)

    # Add html closing
    outstr += '</BODY></HTML>\n'

    return outstr


#################################################
@app.route("/pool/nba")
def poolnba():

    teams = {}
    count = 99

    outstr = ""

    # parse args for year
    year = request.args.get('year','2016', type=str)

    # Open file containing owners and teams
    filename = "nba.teams."+year
    try:
        #ownertext = open(filename).read()
        ownertext = open(os.path.join(os.path.dirname(__file__),filename),'r').read()
    except IOError:
        return filename + " not found"

    # If there are dashes in owner file, it's an auction league
    if ( ownertext.find('-') == -1 ):
        auction = False
    else:
        auction = True

    # split into lines
    lines = ownertext.split("\n")
    betPerGame = float(lines.pop(0))

    # Open ESPN standings page
    url='http://espn.go.com/nba/standings/_/season/' + year 
    #print (url) 
    standingstext=urllib.urlopen(url)
    standings = BeautifulSoup(standingstext)

    # get all the <tr> entries
    for row in standings.findAll('tr'):

        # get all the <td> entries in current row
        for td in row.findAll('td'):

            # get all the <span> entries in this td
            spans = td.findAll('span')

            # If there are 4 or 5 spans, this is a team name.  If 5, there is a playoff key before the name
            if ( len(spans) == 4 or len(spans) == 5 ):
                abbr = spans[len(spans)-2].findAll('abbr')
                teamname = abbr[0].string
                #print teamname
                # W L HG 
                teams[teamname] = [0,0,0]
                count = 0
            else:
                # The 2 <td> entries after the <td> with the team name are w and l
                if ( count < 2 ):
                    #print td.string
                    teams[teamname][count] = int(td.string)
                # 5th td is home w-l record
                elif ( count == 4 ):
                    #print td.string
                    hg = td.string.split("-")
                    teams[teamname][2] = int(hg[0]) + int(hg[1])
                    #print teams[teamname][2]

                count = count + 1


    # read all the owners and their teams
    ownerNames = []
    ownerTeams = {}
    ownerCost = {}
    ownerW = {}
    ownerL = {}
    ownerHomeGames = {}

    # For auction, every line in owner file is formatted as owner:team-cost:team-cost....
    # If not an auction, format is owner:team:team:...
    while ( len(lines) > 0 ):
        # pop next line from file
        ownerLine = lines.pop(0)
        # split by :
        ownerFields = ownerLine.split(":")
        # owner name is first field
        ownerName = ownerFields.pop(0)

        # Skip any empty lines
        if ( ownerName == '' ):
            continue

        ownerNames.append(ownerName)

        # Create dicts for this owner
        # List of teams owned
        ownerTeams[ownerName] = list()
        # Total owner cost
        ownerCost[ownerName] = 0
    
        # Total owner W/L, HG, RS, RA
        ownerW[ownerName] = 0
        ownerL[ownerName] = 0
        ownerHomeGames[ownerName] = 0

        # select all the teams for this owner
        while ( len( ownerFields ) > 0 ):
            if ( auction ):
                # split out the cost and the team name
                teamCost = ownerFields.pop(0).split("-")
                team = teamCost[0]
                cost = teamCost[1]
            else:
                team = ownerFields.pop(0)
                cost = 0
            # print (team, cost)

            if ( team in teams ):
                # Add team to owner list
                ownerTeams[ownerName].append(team)

                # Add cost to owner cost
                ownerCost[ownerName] += int(cost)

                # Add cost to teams dictionary
                teams[team].append(int(cost))

                # Add team record to owner record
                ownerW[ownerName] += teams[team][0]
                ownerL[ownerName] += teams[team][1]
                ownerHomeGames[ownerName] += teams[team][2]


    #for owner in ownerTeams.keys():
        #print owner, ownerCost[owner], ownerW[owner], ownerL[owner], ownerT[owner]
        #for teamname in ownerTeams[owner]:
            #print teamname, teams[teamname][3], teams[teamname][0], teams[teamname][1], teams[team


    # Create HTML object
    h = HTML()

    # Add HTML header info
    #output = 'Content-type: text/html\n\n'
    outstr += '<HTML>\n<HEAD>\n<TITLE>' + year + ' NBA Standings</TITLE>\n<link rel="stylesheet"'
    outstr += ' type="text/css"'
    outstr += ' href="' + url_for('static', filename = 'standings.css') + '"'
    #outstr += ' href="static/standings.css"'
    outstr += '/>\n</HEAD>\n<BODY>\n'


    # Create main HTML table

    t = h.table( caption = str(year) + ' NBA pool standings')

    # Add table header
    t.th('Owner/Team')
    if ( auction ):
        t.th('Cost')
    t.th('W')
    t.th('L')
    t.th('EHGR')


    # Iterate through the owners
    for owner in ownerNames:

        ehgr = ownerW[owner] + ownerL[owner] - ownerHomeGames[owner]*2
        # Create row for owner name and summary
        orow = t.tr()
        orow.th(owner, align='left')
        if ( auction ):
            orow.th(str(ownerCost[owner]), align = 'right')
        orow.th(str(ownerW[owner]), align = 'right')
        orow.th(str(ownerL[owner]), align = 'right')
        orow.th(str(ehgr), align = 'right')
        orow.th("$%5.2f" % (betPerGame * (ownerW[owner] - ownerL[owner])), align = 'right')

        # Create row for each team picked by this owner
        for teamname in ownerTeams[owner]:
            trow = t.tr()
            trow.td(nbaNames[teamname], klass = 'indented')
            if ( auction ):
                trow.td(str(teams[teamname][3]), align = 'right')
            trow.td(str(teams[teamname][0]), align = 'right')
            trow.td(str(teams[teamname][1]), align = 'right')
            ehgr = teams[teamname][0] + teams[teamname][1] - teams[teamname][2]*2
            trow.td(str(ehgr), align = 'right')

    # Add html table to the output string
    outstr += str(t)

    # Add html closing
    outstr += '</BODY></HTML>\n'

    return outstr



#################################################
if __name__ == "__main__":
    app.debug = False

    app.run( )
