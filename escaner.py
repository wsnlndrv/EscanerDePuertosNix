#!/usr/bin/python
# -*- coding: utf-8; -*-

import sys
import socket
import configparser
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QLineEdit, QVBoxLayout, QWidget, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QTextCursor, QTextCharFormat, QFont

class PortScannerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Escáner de Puertos")
        self.setGeometry(100, 100, 200,800)
        self.ip_input = QLineEdit(self)
        self.start_port_input = QLineEdit(self)
        self.end_port_input = QLineEdit(self)
        self.timer_input = QLineEdit(self)
        self.load_settings()
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        self.ip_input.setPlaceholderText("Ingrese la dirección IP")
        layout.addWidget(self.ip_input)
        self.ip_input.setStyleSheet("color: lime;")

        # Leer la última IP guardada en la configuración
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        if "Settings" in self.config:
            last_ip = self.config["Settings"].get("last_ip", "")
            self.ip_input.setText(last_ip)

        self.start_port_input.setPlaceholderText("Ingrese el puerto inicial")
        layout.addWidget(self.start_port_input)
        self.start_port_input.setStyleSheet("color: lime;")

        self.end_port_input.setPlaceholderText("Ingrese el puerto final")
        layout.addWidget(self.end_port_input)
        self.end_port_input.setStyleSheet("color: lime;")

        self.timer_input.setPlaceholderText("Tiempo de espera entre puertos (milisegundos)")
        layout.addWidget(self.timer_input)
        self.timer_input.setStyleSheet("color: lime;")

        self.scan_button = QPushButton("Iniciar Escaneo", self)
        layout.addWidget(self.scan_button)
        self.scan_button.setCheckable(True)
        self.scan_button.clicked.connect(self.toggle_scan)

        self.status_label = QLabel("", self)
        layout.addWidget(self.status_label)

        self.result_textedit = QTextEdit(self)
        layout.addWidget(self.result_textedit)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #000;
                color: #fff;
            }
            QLabel {
                font-size: 14px;
                margin-bottom: 5px;
            }
            QLineEdit, QTextEdit {
                padding: 8px;
                border: 1px solid #fff;
                border-radius: 5px;
                background-color: #333;
                color: #fff;
            }
            QPushButton {
                padding: 10px 20px;
                border: 1px solid #007bff;
                border-radius: 5px;
                background-color: #007bff;
                color: white;
                font-size: 16px;
            }
            QPushButton:checked {
                background-color: #dc3545; /* Rojo */
                border-color: #dc3545;
            }
            QPushButton:hover {
                background-color: #0056b3;
                border-color: #0056b3;
            }
        """)

        self.timer = None

    def toggle_scan(self):
        if self.scan_button.isChecked():
            self.start_scan()
        else:
            self.stop_scan()

    def start_scan(self):
        ip = self.ip_input.text()
        start_port = int(self.start_port_input.text())
        end_port = int(self.end_port_input.text())
        timer_interval = int(self.timer_input.text())

        if not ip or not start_port or not end_port or not timer_interval:
            QMessageBox.critical(self, "Error", "Por favor, complete todos los campos.")
            self.scan_button.setChecked(False)
            return

        self.scanning_ip = ip
        self.current_port = start_port
        self.end_port = end_port
        self.timer_interval = timer_interval

        self.scan_button.setText("Detener Escaneo")

        self.result_textedit.clear()
        self.status_label.setText("Escaneando...")

        self.scan_next_port(start_port)  # Iniciar el escaneo desde el puerto mínimo

    def stop_scan(self):
        if self.timer:
            self.timer.stop()
        self.status_label.setText("Escaneo detenido")
        self.scan_button.setChecked(False)
        self.scan_button.setText("Iniciar Escaneo")

    def scan_next_port(self, port):  
        if not self.scan_button.isChecked():  
            return

        if port <= self.end_port:
            status, _ = self.check_port(self.scanning_ip, port)
            if status == "abierto":
                color = QColor(0, 255, 0)  # Verde: RGB (0, 255, 0)
            else:
                color = QColor(128, 128, 128)  # Rojo: RGB (255, 0, 0)

            self.result_textedit.setTextColor(color)
            self.result_textedit.append(f"Puerto {port}: {status}")

            next_port = port + 1
            self.timer = QTimer.singleShot(self.timer_interval, lambda: self.scan_next_port(next_port))
        else:
            self.status_label.setText("Escaneo completo")
            self.scan_button.setChecked(False)
            self.scan_button.setText("Iniciar Escaneo")

    def check_port(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(int(self.timer_input.text()) / 1000)  # Convertir a segundos
        try:
            result = sock.connect_ex((ip, port))
            if result == 0:
                status = "abierto"
                color = QColor(0, 255, 0)  # Verde: RGB (0, 255, 0)
            else:
                status = "cerrado"
                color = QColor(255, 0, 0)  # Rojo: RGB (255, 0, 0)
        except socket.timeout:
            status = "cerrado"
            color = QColor(255, 0, 0)  # Rojo: RGB (255, 0, 0)
        finally:
            sock.close()
        
        return status, color


    def closeEvent(self, event):
        # Guardar la última IP ingresada y otros valores en la configuración al cerrar la aplicación
        last_ip = self.ip_input.text()
        min_port = self.start_port_input.text()
        max_port = self.end_port_input.text()
        last_timer = self.timer_input.text()

        self.config["Settings"] = {"last_ip": last_ip, "min_port": min_port, "max_port": max_port, "last_timer": last_timer}
        with open("config.ini", "w") as config_file:
            self.config.write(config_file)
        event.accept()
        
    def load_settings(self):
        # Cargar la configuración guardada al iniciar la aplicación
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        if "Settings" in self.config:
            settings = self.config["Settings"]
            self.ip_input.setText(settings.get("last_ip", ""))
            self.start_port_input.setText(settings.get("min_port", ""))
            self.end_port_input.setText(settings.get("max_port", ""))
            self.timer_input.setText(settings.get("last_timer", ""))

def main():
    app = QApplication(sys.argv)
    window = PortScannerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
