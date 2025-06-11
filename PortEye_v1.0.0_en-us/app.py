from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import psutil
import time
import threading
import sqlite3
from datetime import datetime
import sys
import ctypes
import webbrowser
import platform
import signal

# Initialize the Flask application
app = Flask(__name__)
# Enable CORS (Cross - Origin Resource Sharing)
CORS(app)

# Permission check (cross - platform)
def is_admin():
    # Check if the user has administrative privileges
    return ctypes.windll.shell32.IsUserAnAdmin() if platform.system() == 'Windows' else os.geteuid() == 0  # noqa: F821

def request_admin():
    # Request administrative privileges
    if platform.system() == 'Windows':
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    else:
        print("Please run with sudo")
        sys.exit(1)

# Database initialization
def init_db():
    # Connect to the database
    conn = sqlite3.connect('port_monitor.db')
    with conn:
        # Create a table to store port history if it doesn't exist
        conn.execute('''CREATE TABLE IF NOT EXISTS port_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME, port INTEGER, process TEXT, status TEXT)''')
        # Create indexes for the port and process columns
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port ON port_history (port)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_process ON port_history (process)')

# Port monitoring thread
monitor_running = True
def monitor_ports(interval=60):
    prev_ports = {}
    while monitor_running:
        curr_ports = {}
        # Get all listening network connections
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                port = conn.laddr.port
                try:
                    # Get the process name associated with the port
                    proc = psutil.Process(conn.pid).name() if conn.pid else "Unknown process"
                    curr_ports[port] = proc
                except:
                    curr_ports[port] = "Access denied"
        
        with sqlite3.connect('port_monitor.db') as conn:
            c = conn.cursor()
            # Record port opening and closing events
            for p in curr_ports:
                if p not in prev_ports:
                    c.execute("INSERT INTO port_history VALUES (NULL, ?, ?, ?, ?)", 
                            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), p, curr_ports[p], 'opened'))
            for p in prev_ports:
                if p not in curr_ports:
                    c.execute("INSERT INTO port_history VALUES (NULL, ?, ?, ?, ?)", 
                            (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), p, prev_ports[p], 'closed'))
            conn.commit()
        prev_ports = curr_ports
        time.sleep(interval)

# Front - end route
@app.route('/')
def index():
    # Render the index.html template
    return render_template('index.html')

# Current port API (with filtering)
@app.route('/api/ports')
def get_ports():
    # Get filter parameters from the request
    filter_port = request.args.get('port', type=int)
    filter_proc = request.args.get('process', type=str)
    ports = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid) if conn.pid else None
                port_info = {
                    'port': conn.laddr.port,
                    'process': proc.name() if proc else "Unknown process",
                    'cmdline': ' '.join(proc.cmdline()) if proc and proc.cmdline() else "N/A",
                    'cpu_percent': proc.cpu_percent(0.1) if proc else "N/A",
                    'memory_percent': proc.memory_percent() if proc else "N/A"
                }
                # Filter ports based on parameters
                if (not filter_port or port_info['port'] == filter_port) and \
                   (not filter_proc or filter_proc in port_info['process']):
                    ports.append(port_info)
            except:
                continue
    return jsonify(ports)

# History record API (with filtering)
@app.route('/api/history')
def get_history():
    # Get limit and filter parameters from the request
    limit = request.args.get('limit', 100, type=int)
    filter_port = request.args.get('port', type=int)
    filter_proc = request.args.get('process', type=str)
    query = "SELECT * FROM port_history"
    params, conds = [], []
    if filter_port:
        conds.append("port = ?")
        params.append(filter_port)
    if filter_proc:
        conds.append("process LIKE ?")
        params.append(f'%{filter_proc}%')
    if conds:
        query += " WHERE " + " AND ".join(conds)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    with sqlite3.connect('port_monitor.db') as conn:
        conn.row_factory = sqlite3.Row
        history = [dict(row) for row in conn.execute(query, params).fetchall()]
    return jsonify(history)

# Handle signals to stop the monitoring thread
def signal_handler(sig, frame):
    global monitor_running
    print('Stopping the port monitoring thread...')
    monitor_running = False
    # Wait for the monitoring thread to finish
    for thread in threading.enumerate():
        if thread.name == 'port_monitor':
            thread.join()
    print('The port monitoring thread has stopped, the program exits.')
    sys.exit(0)

if __name__ == '__main__':
    if not is_admin() and not app.debug:
        request_admin()
    init_db()
    # Start the port monitoring thread
    monitor_thread = threading.Thread(target=monitor_ports, daemon=True, name='port_monitor')
    monitor_thread.start()
    # Open the application in the browser
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open('http://localhost:5000')), daemon=True).start()
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    app.run(host='0.0.0.0', port=5000, debug=False)