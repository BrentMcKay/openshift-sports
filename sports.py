import urllib
import re

from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/')
#def hello_world():
#    return 'Hello World!'
def main():
    return "Hello, World!"


@app.route("/scores")
def scores():
    outstr = ''

    # parse args for week and year
    year = request.args.get('year','2015', type=str)
    week = request.args.get('week','1', type=str)

    print (year, week)

    # Open ESPN scores page for year and week
    url='http://espn.go.com/nfl/scoreboard/_/year/' + year + '/seasontype/2/week/' + week
    print (url) 
    scoresrc=urllib.urlopen(url)
    scoretext=scoresrc.read()
        
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


if __name__ == "__main__":
    #app.debug = True
    app.run( )
