import sys
import folium
from sqlalchemy.orm import joinedload, sessionmaker
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QGridLayout, QLabel, QSlider, QScrollArea
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from sqlalchemy import func, create_engine
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
from datetime import datetime, timedelta
from db_create import Base, School, City, Timestamp, Street, SmogData  # Ensure db_create is properly referenced

# Database setup
engine = create_engine('postgresql://postgres:adb@localhost:5432/air-pollution')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)

class MapGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.session = Session()
        self.curr_showed_school = None  # For plots
        self.day_offset = 1
        self.initUI()

    def initUI(self):
        # Main layout
        self.main_layout = QGridLayout(self)

        # Folium map setup
        self.map = folium.Map(location=[52.2297, 21.0122], zoom_start=6)
        self.add_school_markers()

        # Map as HTML
        map_html = self.map._repr_html_()
        self.map_view = QWebEngineView()
        QWebEngineSettings.globalSettings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.map_view.setHtml(map_html)

        # Slider for selecting days offset
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(7)
        self.slider.setValue(1)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider_label = QLabel("Day Offset: 1")
        self.slider.valueChanged.connect(self.update_plots)

        # Matplotlib graphs setup
        self.figures = [plt.figure(figsize=(10, 4)) for _ in range(5)]
        self.canvases = [FigureCanvas(fig) for fig in self.figures]
        self.toolbars = [NavigationToolbar(canvas, self) for canvas in self.canvases]

        # Graph layout in a scroll area
        graph_layout = QVBoxLayout()
        for toolbar, canvas in zip(self.toolbars, self.canvases):
            graph_layout.addWidget(toolbar)
            graph_layout.addWidget(canvas)

        scroll_area = QScrollArea()
        scroll_content = QWidget()
        scroll_content.setLayout(graph_layout)
        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)

        # Adding widgets to layout
        self.main_layout.addWidget(self.map_view, 0, 0, 1, 2)
        self.main_layout.addWidget(self.slider, 1, 0)
        self.main_layout.addWidget(self.slider_label, 1, 1)
        self.main_layout.addWidget(scroll_area, 2, 0, 1, 2)

        self.setWindowTitle('Air Quality Monitoring')
        self.setGeometry(100, 100, 1200, 800)

    def add_school_markers(self):
        schools = self.session.query(School).all()
        for school in schools:
            marker = folium.Marker(
                location=[school.latitude, school.longitude],
                tooltip=f"{school.name}",
                icon=folium.Icon(color='green')
            )
            marker.add_to(self.map)
            marker.add_child(folium.Popup(f"<div>School ID: {school.school_id}</div>"))

    def update_plots(self):
        if self.curr_showed_school is None:
            # Placeholder for when no school is selected
            return

        # Fetch smog data
        smog_data = self.session.query(SmogData).filter(SmogData.school_id == self.curr_showed_school).options(joinedload(SmogData.timestamp)).all()
        latest_day = max(data.timestamp.stamp for data in smog_data).split()[0]
        latest_date = datetime.strptime(latest_day, "%Y-%m-%d")
        selected_dates = [(latest_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(self.day_offset)]
        
        mean_pm10_values, mean_pm25_values, mean_humidity_values, mean_temperature_values = [], [], [], []
        hours = []

        for date in selected_dates:
            for data in smog_data:
                if data.timestamp.stamp.startswith(date):
                    hour = int(data.timestamp.stamp[11:13]) + int(data.timestamp.stamp[14:16]) / 60
                    if hour not in hours:
                        hours.append(hour)
                    mean_pm10_values.append(data.pm10)
                    mean_pm25_values.append(data.pm25)
                    mean_humidity_values.append(data.humidity)
                    mean_temperature_values.append(data.temperature)

        x_labels = [f"{int(hour)}h" for hour in sorted(set(hours))]

        # Update plots
        for canvas, fig, data in zip(self.canvases, self.figures, [mean_pm10_values, mean_pm25_values, mean_humidity_values, mean_temperature_values]):
            ax = fig.add_subplot(111)
            ax.scatter(hours, data)
            ax.set_xticks(sorted(set(hours)))
            ax.set_xticklabels(x_labels)
            canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MapGUI()
    gui.show()
    sys.exit(app.exec_())
