import sys
import folium
from sqlalchemy.orm import sessionmaker, joinedload
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSlider, QGridLayout, QLabel, QScrollArea
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from sqlalchemy import create_engine, func
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from datetime import datetime, timedelta
from db_create import Base, School, City, Timestamp, Street, SmogData

# Database setup
engine = create_engine('postgresql://postgres:adb@localhost:5432/air-pollution')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)

class MapGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.initUI()
        self.curr_showed_school = None  # Current selected school ID for plots
        self.day_offset = 1  # Default day offset for data plotting

    def initUI(self):
        # Create the main layout
        self.main_layout = QGridLayout(self)

        # Create the Folium map centered on Poland
        self.map = folium.Map(location=[52.2297, 21.0122], zoom_start=6)
        self.add_school_markers()

        # Convert the map to an HTML string and display it in a QWebEngineView
        map_html = self.map._repr_html_()
        self.map_view = QWebEngineView()
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.map_view.setHtml(map_html)

        # Create a slider for changing the displayed date range
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(7)
        self.slider.setValue(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider_label = QLabel("Day Offset: 1")
        self.slider.valueChanged.connect(self.update_plots)

        # Matplotlib setup for displaying various air quality metrics
        self.fig1, self.canvas1 = self.create_plot()
        self.fig2, self.canvas2 = self.create_plot()
        self.fig3, self.canvas3 = self.create_plot()
        self.fig4, self.canvas4 = self.create_plot()
        self.fig5, self.canvas5 = self.create_plot()

        # Layout for graphs
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.canvas1)
        graph_layout.addWidget(self.canvas2)
        graph_layout.addWidget(self.canvas3)
        graph_layout.addWidget(self.canvas4)
        graph_layout.addWidget(self.canvas5)

        # Scroll area for graphs
        scroll_area = QScrollArea()
        scroll_area.setLayout(graph_layout)
        scroll_area.setWidgetResizable(True)

        # Adding widgets to the main layout
        self.main_layout.addWidget(self.map_view, 0, 0, 1, 2)
        self.main_layout.addWidget(self.slider, 1, 0)
        self.main_layout.addWidget(self.slider_label, 1, 1)
        self.main_layout.addWidget(scroll_area, 2, 0, 1, 2)

        self.setWindowTitle("Poland Air Quality Monitoring")

    def create_plot(self):
        """ Helper function to create a matplotlib plot and canvas. """
        fig = plt.figure(figsize=(10, 4))
        canvas = FigureCanvas(fig)
        return fig, canvas

    def add_school_markers(self):
        """ Add markers for each school to the map with clickable popups. """
        schools = self.session.query(School).all()
        for school in schools:
            marker = folium.Marker(
                [school.latitude, school.longitude],
                popup=f'<b>{school.name}</b>',
                tooltip=school.name,
                icon=folium.Icon(color='green')
            )
            marker.add_to(self.map)

    def update_plots(self):
        """ Update plots based on the selected school and day offset. """
        if not self.curr_showed_school:
            return  # If no school is selected, do nothing

        # Fetch smog data for the current school
        smog_data = self.session.query(SmogData).filter_by(school_id=self.curr_showed_school).options(joinedload(SmogData.timestamp)).all()
        timestamps = [data.timestamp.stamp for data in smog_data]
        data_points = {'PM10': [], 'PM2.5': [], 'Humidity': [], 'Temperature': []}

        for data in smog_data:
            data_points['PM10'].append(data.pm10)
            data_points['PM2.5'].append(data.pm25)
            data_points['Humidity'].append(data.humidity)
            data_points['Temperature'].append(data.temperature)

        # Example plotting logic (this should be customized to fit actual data structures)
        self.plot_data(self.fig1, self.canvas1, timestamps, data_points['PM10'], 'PM10 Average')
        self.plot_data(self.fig2, self.canvas2, timestamps, data_points['PM2.5'], 'PM2.5 Average')
        self.plot_data(self.fig3, self.canvas3, timestamps, data_points['Humidity'], 'Humidity')
        self.plot_data(self.fig4, self.canvas4, timestamps, data_points['Temperature'], 'Temperature')

    def plot_data(self, fig, canvas, timestamps, values, title):
        """ Helper function to plot data on given figure and canvas. """
        ax = fig.add_subplot(111)
        ax.clear()
        ax.plot(timestamps, values)
        ax.set_title(title)
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MapGUI()
    gui.show()
    sys.exit(app.exec_())
