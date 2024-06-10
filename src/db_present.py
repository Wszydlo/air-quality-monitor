import sys
import folium
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QGridLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineSettings

from PyQt5.QtCore import QUrl
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

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

    def initUI(self):
        # Create the main layout
        main_layout = QGridLayout()

        # Create the map
        
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
        html_map = poland_map._repr_html_()
        map_view = QWebEngineView()
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        map_view.setHtml(html_map)

        # Create the timeline slider
        timeline_slider = QSlider(Qt.Horizontal)

        # Create the buttons
        button_layout = QHBoxLayout()
        button1 = QPushButton("Refresh map")
        button2 = QPushButton("Quit")
        button_layout.addWidget(button1)
        button_layout.addWidget(button2)

        # Create the matplotlib graphs
        graph_layout = QVBoxLayout()
        fig1 = plt.figure()
        canvas1 = FigureCanvas(fig1)
        fig2 = plt.figure()
        canvas2 = FigureCanvas(fig2)
        fig3 = plt.figure()
        canvas3 = FigureCanvas(fig3)
        graph_layout.addWidget(canvas1)
        graph_layout.addWidget(canvas2)
        graph_layout.addWidget(canvas3)

        # Add the components to the main layout
        main_layout.addWidget(map_view, 0, 0)
        main_layout.addWidget(timeline_slider, 1, 0)
        main_layout.addLayout(button_layout, 2, 0)
        main_layout.addLayout(graph_layout, 0, 1)

        self.setLayout(main_layout)
        self.setWindowTitle("Poland Map GUI")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    map_gui = MapGUI()
    map_gui.show()
    sys.exit(app.exec_())