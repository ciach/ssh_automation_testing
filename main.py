import modules
from time import sleep







if __name__ == '__main__':
    a = modules.ssh2_ssh_client("192.168.1.104", "root", "odroid")
    a.run_command("df -h")
    a.run_command("df -az")
    a.send_file("test.txt", "/root/test.txt")
    a.get_file("/root/test.txt", "test1.txt")
    # a = modules.paramiko_ssh_client("192.168.1.106", "root", "odroid")
    # a.run_command("df -h")
    # a.run_command("df -az")
    # a.send_file("test.txt", "/root/test.txt")
    # a.get_file("/root/test.txt", "test1.txt")
    # sleep(2)
    # a.close_connection()

