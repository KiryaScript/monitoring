import sys
import psutil
import time
import webbrowser
import platform
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, 
                             QWidget, QFrame, QPushButton, QMessageBox, QTabWidget, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QIcon
import pyqtgraph as pg

class SystemMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced System Monitor")
        self.setGeometry(100, 100, 1000, 700)
        self.is_dark_theme = False
        self.cpu_data = []
        self.memory_data = []
        self.network_download_data = []
        self.network_upload_data = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Top panel with buttons
        top_panel = QHBoxLayout()
        self.theme_button = QPushButton("Dark Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        self.info_button = QPushButton("About")
        self.info_button.clicked.connect(self.show_info)
        self.website_button = QPushButton("Website")
        self.website_button.clicked.connect(self.open_website)

        top_panel.addWidget(self.theme_button)
        top_panel.addWidget(self.info_button)
        top_panel.addWidget(self.website_button)
        top_panel.addStretch(1)

        main_layout.addLayout(top_panel)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_monitor_tab(), "Monitor")
        self.tabs.addTab(self.create_network_tab(), "Network")
        self.tabs.addTab(self.create_system_info_tab(), "System Info")

        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)  # Update every second

        self.last_net_io = psutil.net_io_counters()
        self.last_time = time.time()

        self.set_theme()

    def create_monitor_tab(self):
        tab = QWidget()
        layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # Frames for info sections
        cpu_frame = QFrame()
        memory_frame = QFrame()
        network_frame = QFrame()
        power_frame = QFrame()

        cpu_layout = QVBoxLayout(cpu_frame)
        memory_layout = QVBoxLayout(memory_frame)
        network_layout = QVBoxLayout(network_frame)
        power_layout = QVBoxLayout(power_frame)

        # Labels for info
        self.cpu_info = QLabel()
        self.memory_info = QLabel()
        self.network_info = QLabel()
        self.power_info = QLabel()

        cpu_layout.addWidget(self.cpu_info)
        memory_layout.addWidget(self.memory_info)
        network_layout.addWidget(self.network_info)
        power_layout.addWidget(self.power_info)

        left_layout.addWidget(cpu_frame)
        left_layout.addWidget(memory_frame)
        left_layout.addWidget(network_frame)
        left_layout.addWidget(power_frame)

        # Graphs
        self.cpu_plot = pg.PlotWidget(title="CPU Usage")
        self.cpu_plot.setYRange(0, 100)
        self.cpu_curve = self.cpu_plot.plot(pen=pg.mkPen(color=(0, 114, 178), width=2))

        self.memory_plot = pg.PlotWidget(title="Memory Usage")
        self.memory_plot.setYRange(0, 100)
        self.memory_curve = self.memory_plot.plot(pen=pg.mkPen(color=(0, 158, 115), width=2))

        self.network_plot = pg.PlotWidget(title="Network Usage")
        self.network_plot.setYRange(0, 100)
        self.network_download_curve = self.network_plot.plot(pen=pg.mkPen(color=(0, 114, 178), width=2))
        self.network_upload_curve = self.network_plot.plot(pen=pg.mkPen(color=(213, 94, 0), width=2))

        right_layout.addWidget(self.cpu_plot)
        right_layout.addWidget(self.memory_plot)
        right_layout.addWidget(self.network_plot)

        layout.addLayout(left_layout, 1)
        layout.addLayout(right_layout, 2)
        tab.setLayout(layout)
        return tab

    def create_network_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels(["Local Address", "Local Port", "Remote Address", "Remote Port", "Status"])
        layout.addWidget(self.connections_table)
        tab.setLayout(layout)
        return tab

    def create_system_info_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        self.system_info = QLabel()
        layout.addWidget(self.system_info)
        tab.setLayout(layout)
        self.update_system_info()
        return tab

    def update_stats(self):
        self.update_cpu_stats()
        self.update_memory_stats()
        self.update_network_stats()
        self.update_power_stats()
        self.update_network_connections()

    def update_cpu_stats(self):
        cpu_percent = psutil.cpu_percent()
        cpu_freq = psutil.cpu_freq()
        try:
            cpu_temp = psutil.sensors_temperatures()['coretemp'][0].current
        except:
            cpu_temp = "N/A"
        self.cpu_info.setText(f"CPU Usage: {cpu_percent}%\n"
                              f"CPU Frequency: {cpu_freq.current:.2f} MHz\n"
                              f"CPU Temperature: {cpu_temp}°C")
        self.cpu_data.append(cpu_percent)
        self.cpu_curve.setData(self.cpu_data[-100:])

    def update_memory_stats(self):
        memory = psutil.virtual_memory()
        self.memory_info.setText(f"Memory Usage: {memory.percent}%\n"
                                 f"Used: {self.format_bytes(memory.used)}\n"
                                 f"Available: {self.format_bytes(memory.available)}")
        self.memory_data.append(memory.percent)
        self.memory_curve.setData(self.memory_data[-100:])

    def update_network_stats(self):
        net_io = psutil.net_io_counters()
        current_time = time.time()
        time_elapsed = current_time - self.last_time

        download_speed = (net_io.bytes_recv - self.last_net_io.bytes_recv) / time_elapsed
        upload_speed = (net_io.bytes_sent - self.last_net_io.bytes_sent) / time_elapsed

        self.network_info.setText(f"Network:\n"
                                  f"Download: {self.format_bytes(download_speed)}/s\n"
                                  f"Upload: {self.format_bytes(upload_speed)}/s")

        self.network_download_data.append(download_speed)
        self.network_upload_data.append(upload_speed)
        self.network_download_curve.setData(self.network_download_data[-100:])
        self.network_upload_curve.setData(self.network_upload_data[-100:])

        self.last_net_io = net_io
        self.last_time = current_time

    def update_power_stats(self):
        battery = psutil.sensors_battery()
        if battery:
            power_plugged = "Plugged In" if battery.power_plugged else "On Battery"
            self.power_info.setText(f"Power:\n"
                                    f"Battery: {battery.percent}%\n"
                                    f"Status: {power_plugged}")
        else:
            self.power_info.setText("Power information not available")

    def update_network_connections(self):
        connections = psutil.net_connections()
        self.connections_table.setRowCount(len(connections))
        for i, conn in enumerate(connections):
            self.connections_table.setItem(i, 0, QTableWidgetItem(conn.laddr.ip))
            self.connections_table.setItem(i, 1, QTableWidgetItem(str(conn.laddr.port)))
            if conn.raddr:
                self.connections_table.setItem(i, 2, QTableWidgetItem(conn.raddr.ip))
                self.connections_table.setItem(i, 3, QTableWidgetItem(str(conn.raddr.port)))
            self.connections_table.setItem(i, 4, QTableWidgetItem(conn.status))

    def update_system_info(self):
        uname = platform.uname()
        self.system_info.setText(f"System: {uname.system}\n"
                                 f"Node Name: {uname.node}\n"
                                 f"Release: {uname.release}\n"
                                 f"Version: {uname.version}\n"
                                 f"Machine: {uname.machine}\n"
                                 f"Processor: {uname.processor}")

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.set_theme()

    def set_theme(self):
        if self.is_dark_theme:
            self.setStyleSheet("""
                QMainWindow, QFrame, QTabWidget, QTableWidget {
                    background-color: #2E2E2E;
                    color: #FFFFFF;
                }
                QLabel {
                    color: #FFFFFF;
                }
                QPushButton {
                    background-color: #3D3D3D;
                    color: #FFFFFF;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #4D4D4D;
                }
            """)
            self.theme_button.setText("Light Theme")
            for plot in [self.cpu_plot, self.memory_plot, self.network_plot]:
                plot.setBackground('#2E2E2E')
                plot.getAxis('bottom').setPen(pg.mkPen(color='#FFFFFF'))
                plot.getAxis('left').setPen(pg.mkPen(color='#FFFFFF'))
                plot.getAxis('bottom').setTextPen(pg.mkPen(color='#FFFFFF'))
                plot.getAxis('left').setTextPen(pg.mkPen(color='#FFFFFF'))
        else:
            self.setStyleSheet("""
                QMainWindow, QFrame, QTabWidget, QTableWidget {
                    background-color: #F0F0F0;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QPushButton {
                    background-color: #E0E0E0;
                    color: #000000;
                    border: none;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #D0D0D0;
                }
            """)
            self.theme_button.setText("Dark Theme")
            for plot in [self.cpu_plot, self.memory_plot, self.network_plot]:
                plot.setBackground('w')
                plot.getAxis('bottom').setPen(pg.mkPen(color='#000000'))
                plot.getAxis('left').setPen(pg.mkPen(color='#000000'))
                plot.getAxis('bottom').setTextPen(pg.mkPen(color='#000000'))
                plot.getAxis('left').setTextPen(pg.mkPen(color='#000000'))

    def show_info(self):
        QMessageBox.information(self, "About System Monitor", 
                                "Advanced System Monitor v1.0\n"
                                "Created by Devorsky\n"
                                "This application monitors system resources in real-time.")

    def open_website(self):
        webbrowser.open("https://github.com/KiryaScript")

    def format_bytes(self, bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes < 1024:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a more modern look
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())