import requests
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_create import Base, School, City, Timestamp, Street, SmogData

class ApiHandler:
    def __init__(self) -> None:
        # Connect to the database
        self.engine = create_engine('postgresql://postgres:postgres@localhost/air-pollution')
        Base.metadata.bind = self.engine
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def fetch_data(self):
        # Fetch data from the API
        response = requests.get('https://public-esa.ose.gov.pl/api/v1/smog/0')
        return response.json()
    
    def insert_to_database(self, data):
        # Insert data into the database
        for item in data['smog_data']:
            # Create or get the city
            city_name = item['school']['city']
            city = self.session.query(City).filter_by(name=city_name).one_or_none()
            if not city:
                city = City(name=city_name)
                self.session.add(city)
                self.session.flush()  # Flush to get the city_id

            # Create or get the street
            street_name = item['school']['street']
            street_post_code = item['school']['post_code']
            street = self.session.query(Street).filter_by(name=street_name, post_code=street_post_code, city_id=city.city_id).one_or_none()
            if not street:
                street = Street(name=street_name, post_code=street_post_code, city_id=city.city_id)
                self.session.add(street)
                self.session.flush()  # Flush to get the street_id

            # Create or get the school
            school_name = item['school']['name']
            school_longitude = item['school']['longitude']
            school_latitude = item['school']['latitude']
            school = self.session.query(School).filter_by(name=school_name, street_id=street.street_id, city_id=city.city_id).one_or_none()
            if not school:
                school = School(name=school_name, longitude=school_longitude, latitude=school_latitude, street_id=street.street_id, city_id=city.city_id)
                self.session.add(school)
                self.session.flush()  # Flush to get the school_id

            # Create the timestamp
            stamp = item['timestamp']

            timestamp = self.session.query(Timestamp).filter_by(stamp=stamp).one_or_none()
            if not timestamp:
                timestamp = Timestamp(stamp=stamp)
                self.session.add(timestamp)
                self.session.flush()
            else:
                #check if data already added
                data_duplicate = self.session.query(SmogData).filter_by(school_id=school.school_id, stamp_id=timestamp.stamp_id).one_or_none()
                if data_duplicate:
                    print(f"Duplicate detected: timestamp_id={timestamp.stamp_id}\tschool_id={school.school_id}")
                    self.session.commit()
                    return
            
            # Create the smog data
            humidity = item['data']['humidity_avg']
            pressure = item['data']['pressure_avg']
            temperature = item['data']['temperature_avg']
            pm10 = item['data']['pm10_avg']
            pm25 = item['data']['pm25_avg']
            smog_data = SmogData(school_id=school.school_id, stamp_id=timestamp.stamp_id, humidity=humidity, pressure=pressure, temperature=temperature, pm10=pm10, pm25=pm25)
            self.session.add(smog_data)
            self.session.commit()
    
    def update_database(self):
        self.insert_to_database(self.fetch_data())

    