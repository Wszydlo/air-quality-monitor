import sys
import folium
from sqlalchemy.orm import joinedload
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSlider, QGridLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from sqlalchemy import func
from PyQt5 import QtCore
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
        self.fig1 = plt.figure()
        self.canvas1 = FigureCanvas(self.fig1)
        self.fig2 = plt.figure()
        self.canvas2 = FigureCanvas(self.fig2)
        self.fig3 = plt.figure()
        self.canvas3 = FigureCanvas(self.fig3)
        graph_layout.addWidget(self.canvas1)
        graph_layout.addWidget(self.canvas2)
        graph_layout.addWidget(self.canvas3)

        # Add the components to the main layout
        main_layout.addWidget(map_view, 0, 0)
        main_layout.addWidget(timeline_slider, 1, 0)
        main_layout.addLayout(button_layout, 2, 0)
        main_layout.addLayout(graph_layout, 0, 1)

        self.setLayout(main_layout)
        self.setWindowTitle("Poland Map GUI")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(6000) 

    def update_plots(self):
        session = Session()
        smog_data = session.query(SmogData).options(joinedload(SmogData.timestamp)).all()
        timestamps = sorted(set([data.timestamp.stamp for data in smog_data]))
        mean_pm10_values = []
        mean_pm25_values = []

        for timestamp_str in timestamps:
            timestamp_data = [data for data in smog_data if data.timestamp.stamp == timestamp_str]
            pm10_values = [data.pm10 for data in timestamp_data if data.pm10 is not None]
            pm25_values = [data.pm25 for data in timestamp_data if data.pm25 is not None]
            mean_pm10 = sum(pm10_values) / len(pm10_values) if pm10_values else None
            mean_pm25 = sum(pm25_values) / len(pm25_values) if pm25_values else None
            mean_pm10_values.append(mean_pm10)
            mean_pm25_values.append(mean_pm25)
        # for timestamp in timestamps:
        #     mean_pm10 = session.query(func.avg(SmogData.pm10)) \
        #                    .join(Timestamp, SmogData.stamp_id == Timestamp.stamp_id) \
        #                    .filter(Timestamp.stamp == timestamp) \
        #                    .scalar()
        #     mean_pm25 = session.query(func.avg(SmogData.pm25)) \
        #                     .join(Timestamp, SmogData.stamp_id == Timestamp.stamp_id) \
        #                     .filter(Timestamp.stamp == timestamp) \
        #                     .scalar()
        #     mean_pm10_values.append(mean_pm10)
        #     mean_pm25_values.append(mean_pm25)
            # max_pm10 = session.query(func.max(SmogData.pm10)).filter(SmogData.timestamp.has(stamp=timestamp)).scalar()
            # max_pm25 = session.query(func.max(SmogData.pm25)).filter(SmogData.timestamp.has(stamp=timestamp)).scalar()
        session.close()

        # Clear the figure canvases
        self.fig1.clear()
        self.fig2.clear()
        self.fig3.clear()

        # Create subplots and plot the data
        ax1 = self.fig1.add_subplot(111)
        ax1.plot(timestamps, mean_pm10_values, label='Mean PM10')
        ax1.set_xlabel('Timestamp')
        ax1.set_title('Mean PM10')

        ax2 = self.fig2.add_subplot(111)
        ax2.plot(timestamps, mean_pm25_values, label='Mean PM25')
        ax2.set_xlabel('Timestamp')
        ax2.set_title('Mean PM25')

        ax3 = self.fig3.add_subplot(111)
        ax3.set_xlabel('Timestamp')
        ax3.plot(timestamps, timestamps, label='Max PM10')
        ax3.plot(timestamps, timestamps, label='Max PM25')
        ax3.set_title('Max PM10 and PM25')
        ax3.legend()

        # Refresh the figure canvases
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    map_gui = MapGUI()
    map_gui.show()
    sys.exit(app.exec_())