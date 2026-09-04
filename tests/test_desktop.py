import subprocess

from desktop import stop_server


def test_stop_server_terminates_process_group():
    server = subprocess.Popen(["sleep", "30"], start_new_session=True)

    stop_server(server)

    assert server.poll() is not None
