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

app = Flask(__name__)
CORS(app)

# 权限检查（跨平台）
def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin() if platform.system() == 'Windows' else os.geteuid() == 0  # noqa: F821

def request_admin():
    if platform.system() == 'Windows':
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()
    else:
        print("请使用sudo运行")
        sys.exit(1)

# 数据库初始化
def init_db():
    conn = sqlite3.connect('port_monitor.db')
    with conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS port_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME, port INTEGER, process TEXT, status TEXT)''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_port ON port_history (port)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_process ON port_history (process)')

# 端口监控线程
monitor_running = True
def monitor_ports(interval=60):
    prev_ports = {}
    while monitor_running:
        curr_ports = {}
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'LISTEN':
                port = conn.laddr.port
                try:
                    proc = psutil.Process(conn.pid).name() if conn.pid else "未知进程"
                    curr_ports[port] = proc
                except:
                    curr_ports[port] = "访问被拒绝"
        
        with sqlite3.connect('port_monitor.db') as conn:
            c = conn.cursor()
            # 记录开放/关闭事件
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

# 前端路由
@app.route('/')
def index():
    return render_template('index.html')

# 当前端口API（含过滤）
@app.route('/api/ports')
def get_ports():
    filter_port = request.args.get('port', type=int)
    filter_proc = request.args.get('process', type=str)
    ports = []
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'LISTEN':
            try:
                proc = psutil.Process(conn.pid) if conn.pid else None
                port_info = {
                    'port': conn.laddr.port,
                    'process': proc.name() if proc else "未知进程",
                    'cmdline': ' '.join(proc.cmdline()) if proc and proc.cmdline() else "N/A",
                    'cpu_percent': proc.cpu_percent(0.1) if proc else "N/A",
                    'memory_percent': proc.memory_percent() if proc else "N/A"
                }
                if (not filter_port or port_info['port'] == filter_port) and \
                   (not filter_proc or filter_proc in port_info['process']):
                    ports.append(port_info)
            except:
                continue
    return jsonify(ports)

# 历史记录API（含过滤）
@app.route('/api/history')
def get_history():
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

# 处理信号，停止监控线程
def signal_handler(sig, frame):
    global monitor_running
    print('正在停止端口监控线程...')
    monitor_running = False
    # 等待监控线程结束
    for thread in threading.enumerate():
        if thread.name == 'port_monitor':
            thread.join()
    print('端口监控线程已停止，程序退出。')
    sys.exit(0)

if __name__ == '__main__':
    if not is_admin() and not app.debug:
        request_admin()
    init_db()
    monitor_thread = threading.Thread(target=monitor_ports, daemon=True, name='port_monitor')
    monitor_thread.start()
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open('http://localhost:5000')), daemon=True).start()
    # 注册信号处理函数
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    app.run(host='0.0.0.0', port=5000, debug=False)