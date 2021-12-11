import logging
import paramiko
import socket
from datetime import datetime
from os import path
from rich.console import Console
from rich.traceback import install
from rich import print
from sys import stdout
from time import sleep
from rich.progress import track

install()
console = Console(record=True)

# ["192.168.1.104", "192.168.1.106", "192.168.1.102", "192.168.1.108", "192.168.1.110",]

log_dir = ""

msg_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(filename='example.log', format=msg_format, level="INFO")
root = logging.getLogger('ssh-client')
root.setLevel(logging.INFO)

# handler = logging.StreamHandler(stdout)
# handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter(msg_format)
# handler.setFormatter(formatter)
# root.addHandler(handler)


def check_port(host, port):
    a_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result_of_check = a_socket.connect_ex((host, port))
    if result_of_check == 0:
        print(f"Port {port} at {host} is [bold green]open[/bold green].")
        a_socket.close()
        return True
    else:
        print(f"Port {port} at {host} is [bold red]closed[/bold red].")
        a_socket.close()
        return False


class paramiko_ssh_client:
    """ Class which perform a connection via SSH with one host"""

    def __init__(self, ip, user, passwd, timeout=None):
        """ Class Constructor, initializes the class

        :param ip: str ip of the Host
        :param user: str user where the connection will made
        :param passwd: str password of the user
        """
        self.ip = ip
        self.user = user
        self.passwd = passwd
        self.port = 22
        self.timeout = timeout
        self.client = paramiko.SSHClient()
        # self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())  # Establish default policy to get locally the host key
        try:
            root.info("Connecting to: %s" % self.ip)
            self.client.connect(
                hostname=self.ip,
                port=self.port,
                username=self.user,
                password=self.passwd,
                timeout=self.timeout,
                look_for_keys=False)
            root.info("Connected to %s" % self.ip)
            print(f"[green]Connected to: {self.ip}[/green]")
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            root.exception("Can't connect to: '%s': '%s'", self.ip, e)
            console.print_exception()


    def run_command(self, command):
        """ Run command into the Host

        :param command: str which is going to write in the console of the Host
        """
        print("running command:", command)
        _stdin, _stdout, _stderr = self.client.exec_command(command)
        _stdout.channel.recv_exit_status()  # wait for finishing command
        stderr = _stderr.read().decode("utf8").strip()
        stdout = _stdout.read().decode("utf8").strip()
        return stderr, stdout

    def send_file(self, from_path, to_path):
        """ Send file to a host using SFTP protocol, which is included in SSH

        :param from_path: str Variable which specifies the path where the file is in this pc
        :param to_path: str variable which specifies the path where the file is going to be send
        """
        print("sending file: from", from_path, "to", to_path)
        t = paramiko.Transport((self.ip, 22))
        t.connect(username=self.user, password=self.passwd)
        sftp = paramiko.SFTPClient.from_transport(t)
        # sftp = self.client.open_sftp()
        sftp.put(from_path, to_path)
        return str('File sent from path -> {} to path -> {}'.format(from_path, to_path))

    def get_file(self, from_path, to_path):
        """ Download file to a host using SFTP protocol, which is included in SSH

        :param from_path: str Variable which specifies the path where the file is in this pc
        :param to_path: str variable which specifies the path where the file is going to be send
        """
        print("sending file: from", from_path, "to", to_path)
        t = paramiko.Transport((self.ip, 22))
        t.connect(username=self.user, password=self.passwd)
        sftp = paramiko.SFTPClient.from_transport(t)
        # sftp = self.client.open_sftp()
        sftp.get(from_path, to_path)
        return str('File sent from path -> {} to path -> {}'.format(from_path, to_path))

    def send_all_folder_files(self, origin_folder, destination_folder):
        """ Send all the files from the origin_folder to a host using SFTP protocol.

        :param origin_folder: str Variable which specifies the path where the files are in this pc
        :param destination_folder: str variable which specifies the path where the files are going to be send
        """
        for file in os.listdir(origin_folder):
            self.send_file(path.join(origin_folder, file), path.join(destination_folder, file))

    def close_connection(self):
        """ Close the SSH session with the Host"""
        self.client.close()
        root.info("Disconnecting from %s" % self.ip)
        return str(f'SSH Connection closed to {self.ip}')

    def check_connection(self):
        """
        This will check if the connection is still available.

        Return (bool) : True if it's still alive, False otherwise.
        """
        try:
            self.client.get_transport().is_active()
            return True
        except Exception as e:
            console.print_exception()
            return False


def active_wait_for_dut(dut_ip, max_attempts=100, user='root', passwd='root', connection_timeout=2):
    n_attempts = 1
    while n_attempts <= max_attempts:
        try:
            conn = SSHsender(ip=dut_ip, user=user, passwd=passwd, timeout=connection_timeout)
        except Exception:
            print("Attempting to connect:", n_attempts, "out of", max_attempts, "...")
            n_attempts += 1
            time.sleep(5)
            continue
        else:
            print("DUT is ON")
            conn.close_connection()
            return
    # print("DUT is NOT connected.")
    raise Exception("DUT is NOT connected.")


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    a = paramiko_ssh_client("192.168.1.104", "root", "odroid")
    sleep(5)
    a.close_connection()
    sleep(1)
    a = paramiko_ssh_client("192.168.1.102", "root", "odroid")
    sleep(5)
    a.close_connection()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
