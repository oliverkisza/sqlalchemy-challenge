# Import the dependencies.
import datetime as dt
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///SurfsUp (Challenge 10)/Resources/hawaii.sqlite")

#reflect database into new model
Base = automap_base()

# reflect tables
Base.prepare(autoload_with=engine)
Base.classes.keys()
# save references to each table
stations = Base.classes.station
measurements = Base.classes.measurement

# create session from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
#1. homepage
@app.route("/")
def homepage():
    return (
        f"Available routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )

#2. convert query results from precipitation analysis to a dictionary using date as the key and prcp as the value
# return the JSON representation of dictionary
@app.route("/api/v1.0/precipitation")
def precipitation():
    mrd = session.query(measurements.date).order_by(measurements.date.desc()).first()[0]
    mrd = dt.datetime.strptime(mrd, '%Y-%m-%d')
    year_ago = mrd - dt.timedelta(days=365)

    precipitation_scores = session.query(measurements.date, measurements.prcp).filter(measurements.date >= year_ago).filter(measurements.date <= mrd).all()

    precipitation_dict = {date: prcp for date, prcp in precipitation_scores}

    return jsonify(precipitation_dict)

#3. return JSON list of stations
@app.route("/api/v1.0/stations")
def stations_list():
    stationdata = session.query(stations.station, stations.name).all()

    stationlist = [{"Station ID": station, "Name": name} for station, name in stationdata]

    return jsonify(stationlist)

#4. query dates and temp observations of the most active station for the previous year and return them
@app.route("/api/v1.0/tobs")
def tobs():
    #station_counts = session.query(measurements.station, func.count(measurements.station)).group_by(measurements.station).order_by(func.count(measurements.station).desc()).first()
    station_counts = session.query(measurements.station, func.count(measurements.station)).group_by(measurements.station).order_by(func.count(measurements.station).desc()).all()

    mostactive = station_counts[0][0]

    mrd = session.query(func.max(measurements.date)).scalar()
    mrd = dt.datetime.strptime(mrd, '%Y-%m-%d')
    year_ago = mrd - dt.timedelta(days=365)

    #query to get temp observations
    tobsdata = session.query(measurements.date, measurements.tobs).filter(measurements.station == mostactive).filter(measurements.date >= year_ago).filter(measurements.date <= mrd).all()

    tobslist = [{"Date": date, "Temp": tobs} for date, tobs in tobsdata]
    return jsonify(tobslist)

# 5. return JSON list of min/max/avg temp for a specified start or start & end range
# for a specified start calculate TMIN, TAVG, & TMAX for all the dates >= the start date
# for a specified start and end date calculate TMIN, TAVG, & TMAX for all dates between start and end dates (inclusive)
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def tempstats(start, end=None):
    # if no end given, get stats for given date range
    if end:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')
        end_date = dt.datetime.strptime(end, '%Y-%m-%d')

        #calculate stats for specified date range
        temperature_stats = session.query(func.min(measurements.tobs).label("TMIN"),func.avg(measurements.tobs).label("TAVG"),func.max(measurements.tobs).label("TMAX")).filter(measurements.date >= start_date)\
            .filter(measurements.date <= end_date).all()
        
    else:
        start_date = dt.datetime.strptime(start, '%Y-%m-%d')

        #query calculating temp stats for all dates >= start
        temperature_stats = session.query(func.min(measurements.tobs).label("TMIN"),func.avg(measurements.tobs).label("TAVG"),func.max(measurements.tobs).label("TMAX")).filter(measurements.date >= start_date).all()

    #dict for temp stats
    stats_dict = {"tmin": temperature_stats[0][0], "tavg": temperature_stats[0][1], "tmax": temperature_stats[0][2]}

    # return temperature stats as JSON
    return jsonify(stats_dict)

#run flask app
if __name__ == '__main__':
    app.run(debug=True)
