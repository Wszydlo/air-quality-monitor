import folium
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from db_create import *

# Create the database engine
engine = create_engine('postgresql://postgres:adb@localhost:5432/air-pollution')

# Create the base class for declarative models
Base = declarative_base()


# Create the database session
Session = sessionmaker(bind=engine)
session = Session()

# Create a Folium map centered on Poland
poland_map = folium.Map(location=[52.2297, 21.0122], zoom_start=6)

# Fetch school data from the database
schools = session.query(School).all()

# Add markers for each school to the map
for school in schools:
    folium.Marker(
        location=[school.latitude, school.longitude],
        tooltip=school.name,
        icon=folium.Icon(color='green')
    ).add_to(poland_map)

# Display the map
poland_map.show_in_browser()

# Close the database session
session.close()