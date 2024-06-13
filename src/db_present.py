import sys
import folium
from folium.plugins import MarkerCluster
from sqlalchemy.orm import joinedload
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QGridLayout, QScrollArea, QComboBox, QLabel
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from sqlalchemy import func
from PyQt5 import QtCore
from PyQt5.QtCore import QUrl
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

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

class MapGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.curr_showed_school = None # for plots
        self.day_offset = 1

    def initUI(self):
        # Create the main layout
        main_layout = QGridLayout()

        # Create a Folium map centered on Poland
        self.poland_map = folium.Map(location=[52.2297, 21.0122], zoom_start=6)

        # Call the method to add school markers
        self.add_school_markers()

        # Convert map to HTML
        html_map = self.poland_map._repr_html_()
        map_view = QWebEngineView()
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        map_view.setHtml(html_map)

        # Create the slider
        self.slider_label = QLabel("")
        timeline_slider = QSlider(Qt.Horizontal)
        timeline_slider.setMinimum(1)
        timeline_slider.setMaximum(7)
        timeline_slider.setValue(1)
        timeline_slider.setTickPosition(QSlider.TicksBelow)
        timeline_slider.setTickInterval(1)
        timeline_slider.valueChanged.connect(self.slider_changed)

        # Add the components to the main layout
        main_layout.addWidget(map_view, 0, 0)
        main_layout.addWidget(self.slider_label, 1, 1)
        main_layout.addWidget(timeline_slider, 1, 0)

        self.setLayout(main_layout)
        self.setWindowTitle("Poland Map GUI")

    def add_school_markers(self):
        schools = session.query(School).all()
        for school in schools:
            # Fetch average PM10 and PM25 data
            avg_pm10, avg_pm25 = session.query(func.avg(SmogData.pm10), func.avg(SmogData.pm25)).filter(SmogData.school_id == school.school_id).one_or_none() or (0, 0)
            tooltip_text = f"{school.name}<br>PM10 Avg: {avg_pm10:.2f}, PM25 Avg: {avg_pm25:.2f}"
            color = 'red' if avg_pm10 > 50 or avg_pm25 > 25 else 'orange' if avg_pm10 > 30 or avg_pm25 > 15 else 'green'
            marker = folium.Marker(
                location=[school.latitude, school.longitude],
                tooltip=tooltip_text,
                icon=folium.Icon(color=color)
            )
            marker.add_to(self.poland_map)

    def slider_changed(self, value):
        self.day_offset = value
        # This method would need to be implemented to refresh data based on the slider's position.
        # For example, this could control which data range to display.

if __name__ == '__main__':
    app = QApplication(sys.argv)
    map_gui = MapGUI()
    map_gui.show()
    sys.exit(app.exec_())
