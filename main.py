import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QTextCursor
import pyqtgraph as pg
import serial
from serial.tools import list_ports
from uart import Ui_MainWindow

class SerialCommunicator(QMainWindow, Ui_MainWindow):
    # Signal to communicate data received from the serial port to the main thread
    serial_data_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Initialize variables
        self.serial_port = None
        self.baud_rates = {'4800': 4800, '9600': 9600, '19200': 19200, '38400': 38400, '115200': 115200}
        self.received_data_count = 0  # Variable to keep track of received data count

        # Update UI elements
        self.update_serial_ports()
        self.update_baudrate_combobox()

        # Connect UI buttons to corresponding functions
        self.connect_Button.clicked.connect(self.connect_serial)
        self.send_Button.clicked.connect(self.send_data)
        self.clear_Button.clicked.connect(self.clear_text_browser)

        # Create a thread for reading serial data asynchronously
        self.serial_reader = SerialReader(self)
        self.serial_reader.serial_data_received.connect(self.display_received_data)

        # Create PlotWidget for displaying the graph
        self.plot_widget = pg.PlotWidget(self.centralwidget)
        self.plot_widget.setGeometry(25, 450, 750, 100)  # Adjusted position
        self.plot_data = []  # Start with a value of 0
        self.plot_curve = self.plot_widget.plot(self.plot_data, pen='b')

    def update_serial_ports(self):
        # Update the serial ports available in the UI ComboBox
        self.port_List.addItems([port.device for port in list_ports.comports()])

    def update_baudrate_combobox(self):
        # Update the baud rates available in the UI ComboBox
        self.baud_List.addItems(self.baud_rates.keys())

    def connect_serial(self):
        # Attempt to connect to the selected serial port with the chosen baud rate
        selected_port = self.port_List.currentText()
        selected_baud = self.baud_rates[self.baud_List.currentText()]

        try:
            self.serial_port = serial.Serial(port=selected_port, baudrate=selected_baud, timeout=1)
            self.statusbar.showMessage(f"Connected to {selected_port} with Baudrate {selected_baud}")

            # Configure asynchronous serial data reading
            self.serial_reader.set_serial_port(self.serial_port)
            self.serial_reader.start()
        except Exception as e:
            self.statusbar.showMessage(f"Failed to connect: {str(e)}")

    def send_data(self):
        # Send data to the serial port if it is open
        if self.serial_port and self.serial_port.isOpen():
            data_to_send = self.send_Text.toPlainText() + '\n'
            self.serial_port.write(data_to_send.encode('ascii'))

    def clear_text_browser(self):
        # Clear the QTextBrowser widget
        self.textBrowser.clear()
        self.received_data_count = 0  # Reset the received data count
        self.update_plot()  # Update the plot when clearing the text browser

    def display_received_data(self, data):
        # Display received data in the QTextBrowser
        self.textBrowser.append(f"Received: {data}")

        # Convert a string to a float (assumindo que os valores são sempre no formato "+XX,YY")
        try:
            float_value = float(data.replace(',', '.'))
        except ValueError:
            print("Erro ao converter a string para float.")
            return

        # Adicionar o valor float aos dados do gráfico
        self.plot_data.append(float_value)

        # Update the plot with the new data
        self.plot_curve.setData(self.plot_data)

    def update_plot(self):
        # Update the plot with the received data count
        self.plot_data.append(self.received_data_count)
        self.plot_curve.setData(self.plot_data)

class SerialReader(QThread):
    # Signal to communicate data received from the serial port to the main thread
    serial_data_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port = None

    def set_serial_port(self, serial_port):
        # Set the serial port to be used for reading
        self.serial_port = serial_port

    def run(self):
        # Continuously read data from the serial port and emit the signal with received data
        buffer = b''
        while self.serial_port and self.serial_port.isOpen():
            data = self.serial_port.read(1)
            if data:
                buffer += data
                if data == b'\n':
                    received_str = buffer.decode('ascii')
                    self.serial_data_received.emit(received_str)
                    buffer = b''

if __name__ == "__main__":
    # Application entry point
    app = QApplication(sys.argv)
    main_window = SerialCommunicator()
    main_window.show()
    sys.exit(app.exec_())
