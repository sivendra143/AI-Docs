"""
Check the status of the AI Document Chat application components.
This script provides information about the running services, database, and system resources.
"""
import os
import sys
import json
import time
import psutil
import socket
import platform
import subprocess
from datetime import datetime
from pathlib import Path

def get_system_info():
    """Get basic system information."""
    return {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'python_implementation': platform.python_implementation(),
        'python_compiler': platform.python_compiler(),
    }

def get_memory_usage():
    """Get memory usage information."""
    mem = psutil.virtual_memory()
    return {
        'total': f"{mem.total / (1024**3):.2f} GB",
        'available': f"{mem.available / (1024**3):.2f} GB",
        'used': f"{mem.used / (1024**3):.2f} GB",
        'percent': f"{mem.percent}%"
    }

def get_disk_usage():
    """Get disk usage information for the current directory."""
    usage = psutil.disk_usage('.')
    return {
        'total': f"{usage.total / (1024**3):.2f} GB",
        'used': f"{usage.used / (1024**3):.2f} GB",
        'free': f"{usage.free / (1024**3):.2f} GB",
        'percent': f"{usage.percent}%"
    }

def get_process_info(process_name=None, pid=None):
    """Get information about a running process."""
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline']):
        try:
            if (process_name and process_name.lower() in ' '.join(proc.info['cmdline'] or []).lower()) or \
               (pid and proc.pid == pid):
                return {
                    'pid': proc.pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'create_time': datetime.fromtimestamp(proc.create_time()).strftime('%Y-%m-%d %H:%M:%S'),
                    'cpu_percent': proc.cpu_percent(interval=0.1),
                    'memory_percent': proc.memory_percent(),
                    'memory_info': {
                        'rss': f"{proc.memory_info().rss / (1024**2):.2f} MB",
                        'vms': f"{proc.memory_info().vms / (1024**2):.2f} MB",
                    },
                    'cmdline': ' '.join(proc.cmdline())
                }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

def check_port_in_use(port, host='0.0.0.0'):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def get_app_status(config_path='config.json'):
    """Get the status of the application components."""
    status = {
        'timestamp': datetime.now().isoformat(),
        'system': get_system_info(),
        'memory': get_memory_usage(),
        'disk': get_disk_usage(),
        'services': {}
    }
    
    # Load config to get ports
    port = 5000  # Default port
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                port = int(config.get('server', {}).get('port', port))
        except Exception as e:
            print(f"⚠️  Error loading config: {e}", file=sys.stderr)
    
    # Check if the server is running
    server_running = check_port_in_use(port)
    server_process = get_process_info(process_name='python run_app.py') or \
                    get_process_info(process_name='flask run')
    
    status['services']['web_server'] = {
        'status': 'running' if server_running else 'stopped',
        'port': port,
        'process': server_process
    }
    
    # Check if LM Studio is running (if configured)
    lm_studio = get_process_info(process_name='LM Studio')
    if lm_studio:
        status['services']['lm_studio'] = {
            'status': 'running',
            'process': lm_studio
        }
    
    # Check if Ollama is running (if configured)
    ollama = get_process_info(process_name='ollama')
    if ollama:
        status['services']['ollama'] = {
            'status': 'running',
            'process': ollama
        }
    
    # Check document directory
    docs_dir = 'docs'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                docs_dir = config.get('document_processor', {}).get('docs_folder', docs_dir)
        except Exception:
            pass
    
    docs_count = 0
    if os.path.exists(docs_dir):
        docs_count = len([f for f in os.listdir(docs_dir) 
                         if os.path.isfile(os.path.join(docs_dir, f))])
    
    status['documents'] = {
        'directory': os.path.abspath(docs_dir),
        'count': docs_count,
        'exists': os.path.exists(docs_dir)
    }
    
    # Check vector store
    vector_store_dir = 'vector_store'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                vector_store_dir = config.get('vector_store', {}).get('persist_directory', vector_store_dir)
        except Exception:
            pass
    
    vector_store_exists = os.path.exists(vector_store_dir) and any(os.scandir(vector_store_dir))
    status['vector_store'] = {
        'directory': os.path.abspath(vector_store_dir),
        'exists': os.path.exists(vector_store_dir),
        'initialized': vector_store_exists
    }
    
    return status

def print_status(status, format='text'):
    """Print the status in the specified format."""
    if format == 'json':
        print(json.dumps(status, indent=2))
        return
    
    # Text format
    print(f"\n{'='*60}")
    print(f"📊 AI Document Chat - System Status")
    print(f"{'='*60}")
    print(f"🕒 {status['timestamp']}")
    print(f"💻 {status['system']['system']} {status['system']['release']} ({status['system']['machine']})")
    print(f"🐍 Python {status['system']['python_version']} ({status['system']['python_implementation']})\n")
    
    # System resources
    print(f"💾 Memory: {status['memory']['used']} / {status['memory']['total']} ({status['memory']['percent']} used)")
    print(f"💿 Disk: {status['disk']['used']} / {status['disk']['total']} ({status['disk']['percent']} used)\n")
    
    # Services
    print(f"🌐 Web Server (port {status['services']['web_server']['port']}): "
          f"{'✅ Running' if status['services']['web_server']['status'] == 'running' else '❌ Stopped'}")
    
    if 'lm_studio' in status['services']:
        print(f"🤖 LM Studio: ✅ Running (PID: {status['services']['lm_studio']['process']['pid']})")
    
    if 'ollama' in status['services']:
        print(f"🤖 Ollama: ✅ Running (PID: {status['services']['ollama']['process']['pid']})")
    
    # Documents and vector store
    print(f"\n📂 Documents: {status['documents']['count']} in {status['documents']['directory']}")
    print(f"   {'✅' if status['documents']['exists'] else '❌'} Directory exists")
    
    print(f"\n🔍 Vector Store: {status['vector_store']['directory']}")
    print(f"   {'✅' if status['vector_store']['exists'] else '❌'} Directory exists")
    print(f"   {'✅' if status['vector_store']['initialized'] else '❌'} Initialized")
    
    # Process details if server is running
    if status['services']['web_server']['process']:
        proc = status['services']['web_server']['process']
        print(f"\n🔄 Process Info:")
        print(f"   PID: {proc['pid']}")
        print(f"   CPU: {proc['cpu_percent']}%")
        print(f"   Memory: {proc['memory_info']['rss']} (RSS), {proc['memory_info']['vms']} (VMS)")
        print(f"   Started: {proc['create_time']}")
        print(f"   Cmd: {proc['cmdline']}")
    
    print(f"\n{'='*60}\n")

def main():
    """Parse command line arguments and display status."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check the status of the AI Document Chat application')
    parser.add_argument('--config', default='config.json',
                       help='Path to config file (default: config.json)')
    parser.add_argument('--format', choices=['text', 'json'], default='text',
                       help='Output format (default: text)')
    
    args = parser.parse_args()
    
    try:
        status = get_app_status(args.config)
        print_status(status, args.format)
        return 0
    except Exception as e:
        print(f"❌ Error getting status: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
