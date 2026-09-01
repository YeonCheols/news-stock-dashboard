"""Launch the Streamlit dashboard inside a native desktop window."""

import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import webview


APP_ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.getenv("RADAR_PORT", "8501"))


def wait_for_server(url: str, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1):
                return
        except Exception:
            time.sleep(0.2)
    raise TimeoutError(f"Streamlit 서버가 {timeout:.0f}초 안에 시작되지 않았습니다: {url}")


def is_port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) != 0


def main() -> None:
    if not is_port_available(HOST, PORT):
        raise RuntimeError(f"포트 {PORT}가 이미 사용 중입니다. RADAR_PORT 환경변수로 다른 포트를 지정하세요.")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_ROOT / "app.py"),
        "--server.headless",
        "true",
        "--server.address",
        HOST,
        "--server.port",
        str(PORT),
        "--browser.gatherUsageStats",
        "false",
    ]
    server = subprocess.Popen(command, cwd=APP_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    url = f"http://{HOST}:{PORT}"
    try:
        wait_for_server(url)
        webview.create_window("뉴스·주식 레이더", url, width=1280, height=820, min_size=(960, 640))
        webview.start()
    finally:
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


if __name__ == "__main__":
    main()
