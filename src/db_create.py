from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class School(Base):
    __tablename__ = 'schools'
    school_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    street_id = Column(Integer, ForeignKey('streets.street_id'))
    name = Column(String)
    longitude = Column(Float)
    latitude = Column(Float)

    city = relationship('City', back_populates='schools')
    street = relationship('Street', back_populates='schools')
    smog_data = relationship('SmogData', back_populates='school')

class City(Base):
    __tablename__ = 'cities'
    city_id = Column(Integer, primary_key=True)
    name = Column(String)

    schools = relationship('School', back_populates='city')
    streets = relationship('Street', back_populates='city')

class Timestamp(Base):
    __tablename__ = 'timestamps'
    stamp_id = Column(Integer, primary_key=True)
    stamp = Column(String)

    smog_data = relationship('SmogData', back_populates='timestamp')

class Street(Base):
    __tablename__ = 'streets'
    street_id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey('cities.city_id'))
    name = Column(String)
    post_code = Column(String)

    city = relationship('City', back_populates='streets')
    schools = relationship('School', back_populates='street')

class SmogData(Base):
    __tablename__ = 'smog_data'
    smog_data_id = Column(Integer, primary_key=True)
    school_id = Column(Integer, ForeignKey('schools.school_id'))
    stamp_id = Column(Integer, ForeignKey('timestamps.stamp_id'))
    humidity = Column(Float)
    pressure = Column(Float)
    temperature = Column(Float)
    pm10 = Column(Float)
    pm25 = Column(Float)

    school = relationship('School', back_populates='smog_data')
    timestamp = relationship('Timestamp', back_populates='smog_data')

# Create the database
engine = create_engine('postgresql://postgres:adb@localhost:5432/air-pollution')
Base.metadata.create_all(engine)

# Create a session
Session = sessionmaker(bind=engine)
session = Session()