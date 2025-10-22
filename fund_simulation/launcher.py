"""
Professional launcher for Monte Carlo Fund Simulation
Bundles Streamlit app into standalone Windows executable
"""

import sys
import os
import webbrowser
import time
import threading
import subprocess
from pathlib import Path
import socket

# Ensure we're using the bundled resources when frozen
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = sys._MEIPASS
    os.chdir(application_path)
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))


def find_free_port(start_port=8501, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    return start_port  # Fallback


def wait_for_server(port, timeout=30):
    """Wait for Streamlit server to be ready"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def open_browser(port):
    """Open browser after a short delay"""
    time.sleep(2)  # Give server time to fully start
    url = f"http://localhost:{port}"
    print(f"\n🚀 Opening browser to {url}")
    webbrowser.open(url)


def run_streamlit(port):
    """Run Streamlit application"""
    try:
        # Import streamlit here to avoid issues with frozen app
        from streamlit.web import cli as stcli

        # Prepare Streamlit arguments
        sys.argv = [
            "streamlit",
            "run",
            "app.py",
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
            "--server.fileWatcherType=none",
        ]

        # Run Streamlit
        sys.exit(stcli.main())

    except Exception as e:
        print(f"Error starting Streamlit: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)


def main():
    """Main launcher function"""
    print("=" * 60)
    print("  Monte Carlo Fund Simulation")
    print("  Starting application...")
    print("=" * 60)
    print()

    # Find available port
    port = find_free_port()
    print(f"📡 Using port: {port}")

    # Start browser opener in background thread
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()

    # Run Streamlit (blocks until app closes)
    print("🔧 Starting server...")
    run_streamlit(port)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Application stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)
