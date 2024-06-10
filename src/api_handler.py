import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_create import Base, School, City, Timestamp, Street, SmogData

# Connect to the database
engine = create_engine('postgresql://postgres:adb@localhost/air-pollution')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()
# Fetch data from the API
response = requests.get('https://public-esa.ose.gov.pl/api/v1/smog/0')
data = response.json()
# Insert data into the database
for item in data['smog_data']:
    # Create or get the city
    city_name = item['school']['city']
    city = session.query(City).filter_by(name=city_name).one_or_none()
    if not city:
        city = City(name=city_name)
        session.add(city)
        session.flush()  # Flush to get the city_id

    # Create or get the street
    street_name = item['school']['street']
    street_post_code = item['school']['post_code']
    street = session.query(Street).filter_by(name=street_name, post_code=street_post_code, city_id=city.city_id).one_or_none()
    if not street:
        street = Street(name=street_name, post_code=street_post_code, city_id=city.city_id)
        session.add(street)
        session.flush()  # Flush to get the street_id

    # Create or get the school
    school_name = item['school']['name']
    school_longitude = item['school']['longitude']
    school_latitude = item['school']['latitude']
    school = session.query(School).filter_by(name=school_name, street_id=street.street_id, city_id=city.city_id).one_or_none()
    if not school:
        school = School(name=school_name, longitude=school_longitude, latitude=school_latitude, street_id=street.street_id, city_id=city.city_id)
        session.add(school)
        session.flush()  # Flush to get the school_id

    # Create the timestamp
    stamp = item['timestamp']

    timestamp = session.query(Timestamp).filter_by(stamp=stamp).one_or_none()
    if not timestamp:
        timestamp = Timestamp(stamp=stamp)
        session.add(timestamp)
        session.flush()
    
    # Create the smog data
    humidity = item['data']['humidity_avg']
    pressure = item['data']['pressure_avg']
    temperature = item['data']['temperature_avg']
    pm10 = item['data']['pm10_avg']
    pm25 = item['data']['pm25_avg']
    smog_data = SmogData(school_id=school.school_id, stamp_id=timestamp.stamp_id, humidity=humidity, pressure=pressure, temperature=temperature, pm10=pm10, pm25=pm25)
    session.add(smog_data)
    session.commit()

    