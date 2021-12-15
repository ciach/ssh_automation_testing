import logging
import os
import paramiko
import socket
# import sys
from datetime import datetime
from rich.console import Console
from rich.theme import Theme
from rich.traceback import install
from rich import print
from ssh2.session import Session
from ssh2.sftp import LIBSSH2_FXF_CREAT, LIBSSH2_FXF_WRITE, \
    LIBSSH2_SFTP_S_IRUSR, LIBSSH2_SFTP_S_IRGRP, LIBSSH2_SFTP_S_IWUSR, \
    LIBSSH2_SFTP_S_IROTH, LIBSSH2_FXF_READ

# from time import sleep
# from rich.progress import track

custom_theme = Theme({
    "info": "dim white",
    "info2": "bold blue_violet",
    "warning": "magenta",
    "danger": "bold red"
})

install()
console = Console(record=True, theme=custom_theme)

logger_file = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_script.log"

msg_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

logging.basicConfig(filename=logger_file, format=msg_format, level="INFO")
logger = logging.getLogger('ssh-client')


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


def get_now_time():
    return str(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


class ssh2_ssh_client:
    def __init__(self, ip, user, passwd, ):
        self.ip = ip
        port = 22
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.ip, port))
        self.session = Session()
        self.session.handshake(sock)
        try:
            self.session.userauth_password(user, passwd)
            time_now = get_now_time()
            console.print(f"[info]{time_now}[/info] | [green]{self.ip}[/green]: Connection established!")
            logger.info("Connected to %s" % self.ip)
        except Session.AuthenticationException as e:
            logger.exception("Can't connect to: '%s': '%s'", self.ip, e)
            console.print_exception()

    def run_command(self, command, timeout=0):
        """ run command and read output """
        self.session.set_timeout(timeout)
        channel = self.session.open_session()
        time_now = get_now_time()
        # channel.shell()
        channel.execute(command, )
        console.print(f"[info]{time_now}[/info] | {self.ip}: Running command: [bold]{command}[/bold]")
        logger.info("Running command: %s @ %s" % (command, self.ip))
        _stdout, _exit_status, _stderr = self._read(channel)
        if len(_stdout) > 0:
            logger.info("Command: %s output from %s:\n %s" % (command, self.ip, _stdout))
        if _stderr != (0, b''):
            logger.error("Command: %s error from %s:\n %s" % (command, self.ip, _stderr))
        channel.close()
        #time_now = get_now_time()
        #console.print(f"[info]{time_now}[/info] | [green]{self.ip}[/green]: Disconnected")
        return None

    def _read(self, channel):
        """ read the content of the channel """
        size, data = channel.read()
        results = ""
        while size > 0:
            results += data.decode("utf-8")
            size, data = channel.read()
        return results, channel.get_exit_status(), channel.read_stderr()

    def send_file(self, from_path, to_path):
        # send file from here to there
        buf_size = 1024 * 1024
        sftp = self.session.sftp_init()
        mode = LIBSSH2_SFTP_S_IRUSR | \
               LIBSSH2_SFTP_S_IWUSR | \
               LIBSSH2_SFTP_S_IRGRP | \
               LIBSSH2_SFTP_S_IROTH
        f_flags = LIBSSH2_FXF_CREAT | LIBSSH2_FXF_WRITE
        fileinfo = os.stat(from_path)
        time_now = get_now_time()

        console.print(f"[info]{time_now}[/info] | [green]{self.ip}[/green]: "
                      f"Starting copy of local file {from_path} to remote {self.ip}:{to_path}")

        now = datetime.now()
        with open(from_path, 'rb', buf_size) as local_fh, \
                sftp.open(to_path, f_flags, mode) as remote_fh:
            data = local_fh.read(buf_size)
            while data:
                remote_fh.write(data)
                data = local_fh.read(buf_size)
        taken = datetime.now() - now
        rate = (fileinfo.st_size / 1024000.0) / taken.total_seconds()
        console.print(f"[info]{time_now}[/info] | [green]{self.ip}[/green]: "
                      f"Finished writing remote file in {taken}, transfer rate {rate} MB/s")
        logger.info('File sent from path -> %s to path -> %s with %s' % (from_path, to_path, self.ip))

    def get_file(self, from_path, to_path):
        # send file from there to here
        sftp = self.session.sftp_init()
        with sftp.open(from_path,
                       LIBSSH2_FXF_READ, LIBSSH2_SFTP_S_IRUSR) as remote_fh, \
                open(to_path, 'wb') as local_fh:
            for size, data in remote_fh:
                local_fh.write(data)
        logger.info('File get from path -> %s to path -> %s with %s' % (from_path, to_path, self.ip))

    def send_all_folder_files(self, origin_folder, destination_folder):
        for file in os.listdir(origin_folder):
            self.send_file(os.path.join(origin_folder, file), os.path.join(destination_folder, file))

    def close_connection(self):
        pass

class paramiko_ssh_client:
    """ Class which perform a connection via SSH with one host"""

    def __init__(self, ip, user, passwd, timeout=None):
        """ Class Constructor, initializes the class

        :param ip: str ip of the Host
        :param user: str user where the connection will made
        :param passwd: str password of the user
        """
        self.ip = ip
        port = 22
        self.timeout = timeout
        self.client = paramiko.SSHClient()
        # self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(
            paramiko.AutoAddPolicy())  # Establish default policy to get locally the host key
        try:
            logger.info("Connecting to: %s" % self.ip)
            self.client.connect(
                hostname=self.ip,
                port=port,
                username=user,
                password=passwd,
                timeout=self.timeout,
                look_for_keys=False)
            logger.info("Connected to %s" % self.ip)
            time_now = get_now_time()
            console.print(f"[info]{time_now}[/info] | [green]{self.ip}[/green]: Connection established!")
        except paramiko.ssh_exception.NoValidConnectionsError as e:
            logger.exception("Can't connect to: '%s': '%s'", self.ip, e)
            console.print_exception()
        except paramiko.AuthenticationException as e:
            logger.exception("Can't connect to: '%s': '%s'", self.ip, e)
            console.print_exception()

    def run_command(self, command):
        """ Run command into the Host

        :param command: str which is going to write in the console of the Host
        """
        logger.info("Running command: %s @ %s" % (command, self.ip))
        time_now = get_now_time()
        console.print(f"[info]{time_now}[/info] | {self.ip}: Running command: [bold]{command}[/bold]")
        _stdin, _stdout, _stderr = self.client.exec_command(command)
        _stdout.channel.recv_exit_status()  # wait for finishing command
        stderr = _stderr.read().decode("utf8").strip()
        stdout = _stdout.read().decode("utf8").strip()
        if len(stdout) > 0:
            logger.info("Command: %s output from %s:\n %s" % (command, self.ip, stdout))
        if len(stderr) != 0:
            logger.error("Command: %s error from %s:\n %s" % (command, self.ip, stderr))
        return stderr, stdout

    def send_file(self, from_path, to_path):
        """ Send file to a host using SFTP protocol, which is included in SSH

        :param from_path: str Variable which specifies the path where the file is in this pc
        :param to_path: str variable which specifies the path where the file is going to be send
        """
        time_now = get_now_time()
        console.print(
            f"[info]{time_now}[/info] | {self.ip}: Sending file from [info2]{from_path}[/info2] to [bold]{to_path}[/bold]")
        t = paramiko.Transport((self.ip, 22))
        t.connect(username=self.user, password=self.passwd)
        sftp = paramiko.SFTPClient.from_transport(t)
        # sftp = self.client.open_sftp()
        sftp.put(from_path, to_path)
        logger.info('File sent from path -> %s to path -> %s with %s' % (from_path, to_path, self.ip))
        return str('File sent from path -> {} to path -> {}'.format(from_path, to_path))

    def send_all_folder_files(self, origin_folder, destination_folder):
        """ Send all the files from the origin_folder to a host using SFTP protocol.

        :param origin_folder: str Variable which specifies the path where the files are in this pc
        :param destination_folder: str variable which specifies the path where the files are going to be send
        """
        for file in os.listdir(origin_folder):
            self.send_file(os.path.join(origin_folder, file), os.path.join(destination_folder, file))

    def get_file(self, from_path, to_path):
        """ Download file to a host using SFTP protocol, which is included in SSH

        :param from_path: str Variable which specifies the path where the file is in this pc
        :param to_path: str variable which specifies the path where the file is going to be send
        """
        time_now = get_now_time()
        console.print(
            f"[info]{time_now}[/info] | {self.ip}: Getting file from [bold]{from_path}[/bold] to [info2]{to_path}[/info2]")
        t = paramiko.Transport((self.ip, 22))
        t.connect(username=self.user, password=self.passwd)
        sftp = paramiko.SFTPClient.from_transport(t)
        # sftp = self.client.open_sftp()
        sftp.get(from_path, to_path)
        logger.info('File get from path -> %s to path -> %s with %s' % (from_path, to_path, self.ip))
        return str('File sent from path -> {} to path -> {}'.format(from_path, to_path))

    def close_connection(self):
        """ Close the SSH session with the Host"""
        self.client.close()
        logger.info("Disconnecting from %s" % self.ip)
        time_now = get_now_time()
        console.print(f"[info]{time_now}[/info] | [green]{self.ip}[/green]: Disconnected")
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


"""
def active_wait_for_dut(dut_ip, max_attempts=100, user='root', passwd='root', connection_timeout=2):
    n_attempts = 1
    while n_attempts <= max_attempts:
        try:
            conn = SSHsender(ip=dut_ip, user=user, passwd=passwd, timeout=connection_timeout)
        except Exception:
            print("Attempting to connect:", n_attempts, "out of", max_attempts, "...")
            n_attempts += 1
            sleep(5)
            continue
        else:
            print("DUT is ON")
            conn.close_connection()
            return
    # print("DUT is NOT connected.")
    raise Exception("DUT is NOT connected.")
"""
