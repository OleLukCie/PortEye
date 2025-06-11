# PortEye - Port Monitoring System

PortEye is a port monitoring system developed based on the Python Flask framework. It can monitor the network ports being listened to in the system in real-time and record the opening and closing history of the ports. Through the separation of the front-end and back-end, this system provides a simple and user-friendly web interface, which allows users to easily view port information and historical records.

## Functional Features
- **Real-time Port Monitoring**: Display real-time information about the network ports being listened to in the system, including port numbers, process names, command lines, CPU usage, and memory usage.
- **Port History Records**: Record the opening and closing events of ports. Users can view historical records to understand the usage of ports.
- **Data Filtering**: Support filtering the current port information and historical records by port number and process name, facilitating users to quickly locate the required information.
- **Permission Check**: Automatically check whether administrative privileges are available when running the program to ensure access to the system's network connection information.
- **Signal Handling**: Support `SIGINT` and `SIGTERM` signals. When the program receives these signals, it will stop the port monitoring thread and exit the program.

## Installation and Running

### Environment Requirements
- Python 3.x
- Flask
- Flask-CORS
- psutil
- sqlite3

### Install Dependencies
```bash
pip install flask flask-cors psutil
```

### Run the Program
```bash
python app.py
```

### Notes
- On Windows systems, the program will automatically request administrative privileges; on Linux systems, use `sudo` to run the program.
- After the program starts, it will automatically open the browser to access `http://localhost:5000`.

## Usage

### Current Port Information
- Enter the port number in the "Port Filter" input box to filter out information about the specified port.
- Enter the process name in the "Process Filter" input box to filter out information about the ports occupied by the specified process.
- Click the "Filter" button to display the filtered results.

### Port History Records
- Enter the number of records to display in the "Number of Records to Display" input box.
- Enter the port number in the "Port Filter" input box to filter out historical records of the specified port.
- Enter the process name in the "Process Filter" input box to filter out historical records of the specified process.
- Click the "Filter" button to display the filtered results.

## Project Structure
```
PortEye/
├── app.py              # Back-end code responsible for permission checking, database initialization, port monitoring, and providing API interfaces
├── templates/
│   └── index.html      # Front-end page that interacts with the back-end API through JavaScript to display current port information and port historical records
└── port_monitor.db     # SQLite database used to store the opening and closing history of ports
```

## API Interfaces

### Get Current Port Information
- **URL**: `/api/ports`
- **Method**: `GET`
- **Parameters**:
  - `port`: Optional, port number used to filter information about the specified port.
  - `process`: Optional, process name used to filter information about the ports occupied by the specified process.
- **Return Value**: A JSON array containing information about the currently listened ports.

### Get Port History Records
- **URL**: `/api/history`
- **Method**: `GET`
- **Parameters**:
  - `limit`: Optional, default value is 100, used to specify the number of records to return.
  - `port`: Optional, port number used to filter historical records of the specified port.
  - `process`: Optional, process name used to filter historical records of the specified process.
- **Return Value**: A JSON array containing information about port historical records.

## Contribution
If you are interested in this project, you can contribute code in the following ways:
1. Fork the project.
2. Create your feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push your changes to the remote branch (`git push origin feature/your-feature`).
5. Open a Pull Request.

## License
This project uses the MIT license. Please refer to the [LICENSE](LICENSE) file for details.