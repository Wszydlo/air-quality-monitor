import sys
import folium
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

        # Create the slider
        #self.timeline_combobox = QComboBox()
        self.slider_label = QLabel("")
        timeline_slider = QSlider(Qt.Horizontal)
        timeline_slider.setMinimum(1)
        timeline_slider.setMaximum(7)
        timeline_slider.setValue(1)
        timeline_slider.setTickPosition(QSlider.TicksBelow)
        timeline_slider.setTickInterval(1)
        timeline_slider.valueChanged.connect(self.slider_changed)

        # Create the matplotlib graphs
        graph_layout = QVBoxLayout()
        self.fig1 = plt.figure()
        self.canvas1 = FigureCanvas(self.fig1)
        self.canvas1.setFixedSize(900, 400)
        self.toolbar1 = NavigationToolbar(self.canvas1, self)

        self.fig2 = plt.figure()
        self.canvas2 = FigureCanvas(self.fig2)
        self.canvas2.setFixedSize(900, 400)
        self.toolbar2 = NavigationToolbar(self.canvas2, self)

        self.fig3 = plt.figure()
        self.canvas3 = FigureCanvas(self.fig3)
        self.canvas3.setFixedSize(900, 400)
        self.toolbar3 = NavigationToolbar(self.canvas3, self)

        self.fig4 = plt.figure()
        self.canvas4 = FigureCanvas(self.fig4)
        self.canvas4.setFixedSize(900, 400)
        self.toolbar4 = NavigationToolbar(self.canvas4, self)

        self.fig5 = plt.figure()
        self.canvas5 = FigureCanvas(self.fig5)
        self.canvas5.setFixedSize(900, 400)
        self.toolbar5 = NavigationToolbar(self.canvas5, self)

        graph_layout.addWidget(self.toolbar1)
        graph_layout.addWidget(self.canvas1)
        graph_layout.addWidget(self.toolbar2)
        graph_layout.addWidget(self.canvas2)
        graph_layout.addWidget(self.toolbar3)
        graph_layout.addWidget(self.canvas3)
        graph_layout.addWidget(self.toolbar4)
        graph_layout.addWidget(self.canvas4)
        graph_layout.addWidget(self.toolbar5)
        graph_layout.addWidget(self.canvas5)


        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_content.setLayout(graph_layout)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)

        # Add the components to the main layout
        main_layout.addWidget(map_view, 0, 0)
        main_layout.addWidget(self.slider_label, 1, 1)
        main_layout.addWidget(timeline_slider, 1, 0)
        main_layout.addWidget(scroll_area, 0, 1)

        self.setLayout(main_layout)
        self.setWindowTitle("Poland Map GUI")

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plots)
        self.timer.start(6000)

        self.page = map_view.page()
        self.page.loadFinished.connect(self.on_load_finished)
        self.page.runJavaScript("window.pyObj = { setSchool: function(id) { window.bridge.setSchool(id); } };")

    def on_load_finished(self):
        self.page.runJavaScript("window.pyObj = { setSchool: function(id) { window.bridge.setSchool(id); } };")

    def setSchool(self, school_id):
        self.curr_showed_school = school_id
        self.update_plots()
    
    def slider_changed(self, value):
        self.day_offset = value

    def update_plots(self):
        session = Session()
        smog_data = session.query(SmogData).options(joinedload(SmogData.timestamp)).all()
        self.timestamps = sorted(set([data.timestamp.stamp for data in smog_data]))
        mean_pm10_values = []
        mean_pm25_values = []
        mean_humidity_values = []
        mean_temperature_values = []

        # Clear the figure canvases
        self.fig1.clear()
        self.fig2.clear()
        self.fig3.clear()
        self.fig4.clear()
        self.fig5.clear()

        
        time = []
        latest_day = self.timestamps[-1].split()[0] # latest acquired day
        latest_date = datetime.strptime(latest_day, "%Y-%m-%d")
        selected_dates = [(latest_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(self.day_offset)]
        

        for elem in self.timestamps:
            if elem.split()[0] in selected_dates:
                time.append(elem.split()[1][:-3])
        hours = []
        for t in time:
            h, m = map(int, t.split(':'))
            hours.append(h + m/60)
        x_labels = [f"{i}h" for i in range(0, 25, 3)]
        self.slider_label.setText(f"{selected_dates[-1]} to {selected_dates[0]}")

        if self.curr_showed_school is None:
            # Show data for the whole country
            for timestamp_str in self.timestamps:
                if timestamp_str.split()[0] in selected_dates:
                    timestamp_data = [data for data in smog_data if data.timestamp.stamp == timestamp_str]
                    pm10_values = [data.pm10 for data in timestamp_data if data.pm10 is not None]
                    pm25_values = [data.pm25 for data in timestamp_data if data.pm25 is not None]
                    humidity_values = [data.humidity for data in timestamp_data if data.humidity is not None]
                    temperature_values = [data.temperature for data in timestamp_data if data.temperature is not None]
                    mean_pm10 = sum(pm10_values) / len(pm10_values) if pm10_values else None
                    mean_pm25 = sum(pm25_values) / len(pm25_values) if pm25_values else None
                    mean_humidity = sum(humidity_values) / len(humidity_values) if humidity_values else None
                    mean_temperature = sum(temperature_values) / len(temperature_values) if temperature_values else None
                    if mean_pm10 is not None:
                        mean_pm10_values.append(mean_pm10)
                    if mean_pm25 is not None:
                        mean_pm25_values.append(mean_pm25)
                    if mean_humidity is not None:
                        mean_humidity_values.append(mean_humidity)
                    if mean_temperature is not None:
                        mean_temperature_values.append(mean_temperature)
        else:
            # Show data for the specific school
            for timestamp_str in self.timestamps:
                timestamp_data = [data for data in smog_data if data.timestamp.stamp == timestamp_str and data.school_id == self.curr_showed_school]
                pm10_values = [data.pm10 for data in timestamp_data if data.pm10 is not None]
                pm25_values = [data.pm25 for data in timestamp_data if data.pm25 is not None]
                humidity_values = [data.humidity for data in timestamp_data if data.humidity is not None]
                temperature_values = [data.temperature for data in timestamp_data if data.temperature is not None]
                mean_pm10 = sum(pm10_values) / len(pm10_values) if pm10_values else None
                mean_pm25 = sum(pm25_values) / len(pm25_values) if pm25_values else None
                mean_humidity = sum(humidity_values) / len(humidity_values) if humidity_values else None
                mean_temperature = sum(temperature_values) / len(temperature_values) if temperature_values else None
                if mean_pm10 is not None:
                    mean_pm10_values.append(mean_pm10)
                if mean_pm25 is not None:
                    mean_pm25_values.append(mean_pm25)
                if mean_humidity is not None:
                    mean_humidity_values.append(mean_humidity)
                if mean_temperature is not None:
                    mean_temperature_values.append(mean_temperature)

        session.close()

        # Create subplots and plot the data
        ax1 = self.fig1.add_subplot(111)
        ax1.scatter(hours, mean_pm10_values, label='Mean PM10')
        ax1.set_xlabel('Timestamp')
        ax1.set_title(fr'$\bf{{Mean\ PM10}}$ {selected_dates[-1]} to {selected_dates[0]}')
        ax1.legend(loc='best')
        ax1.set_xticks(range(0, 25, 3))
        ax1.set_xticklabels(x_labels)

        ax2 = self.fig2.add_subplot(111)
        ax2.scatter(hours, mean_pm25_values, label='Mean PM25')
        ax2.set_xlabel('Timestamp')
        ax2.set_title(fr'$\bf{{Mean\ PM25}}$ {selected_dates[-1]} to {selected_dates[0]}')
        ax2.legend(loc='best')
        ax2.set_xticks(range(0, 25, 3))
        ax2.set_xticklabels(x_labels)

        ax3 = self.fig3.add_subplot(111)
        ax3.set_xlabel('Timestamp')
        ax3.scatter(hours, hours, label='Max PM10')
        ax3.scatter(hours, hours, label='Max PM25')
        ax3.set_title(fr'$\bf{{Max\ PM10\ and\ PM25}}$ {selected_dates[-1]} to {selected_dates[0]}')
        ax3.legend(loc='best')
        ax3.set_xticks(range(0, 25, 3))
        ax3.set_xticklabels(x_labels)

        ax4 = self.fig4.add_subplot(111)
        ax4.scatter(hours, mean_humidity_values, label='Mean Humidity')
        ax4.set_xlabel('Timestamp')
        ax4.set_title(fr'$\bf{{Mean\ Humidity}}$ {selected_dates[-1]} to {selected_dates[0]}')
        ax4.legend(loc='best')
        ax4.set_xticks(range(0, 25, 3))
        ax4.set_xticklabels(x_labels)

        ax5 = self.fig5.add_subplot(111)
        ax5.scatter(hours, mean_temperature_values, label='Mean Temperature')
        ax5.set_xlabel('Timestamp')
        ax5.set_title(fr'$\bf{{Mean\ Temperature}}$ {selected_dates[-1]} to {selected_dates[0]}')
        ax5.legend(loc='best')
        ax5.set_xticks(range(0, 25, 3))
        ax5.set_xticklabels(x_labels)

        # Refresh the figure canvases
        self.canvas1.draw()
        self.canvas2.draw()
        self.canvas3.draw()
        self.canvas4.draw()
        self.canvas5.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    map_gui = MapGUI()
    map_gui.show()
    sys.exit(app.exec_())