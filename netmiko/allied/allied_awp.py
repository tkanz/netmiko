from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer
import os


class AlliedSSH(CiscoSSHConnection):
    """Support for AlliedWare plus."""
    def session_preparation(self):
        """Prepare the session after the connection has been established."""
        self._test_channel_read(pattern=r'[>#]')
        self.set_base_prompt()
        self.enable()
        self.disable_paging()
        # Clear the read buffer
        time.sleep(.3 * self.global_delay_factor)
        self.clear_buffer()

    def save_config(self, cmd='write mem', confirm=False):
        """Saves Config Using Copy Run Start"""
        return super(AlliedSSH, self).save_config(cmd=cmd, confirm=confirm)


class AlliedFileTransfer(BaseFileTransfer):
    """AlliedWare SCP File Transfer driver."""
    def __init__(self, ssh_conn, source_file, dest_file, file_system='flash:', direction='put'):
        self.ssh_ctl_chan = ssh_conn
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        return super(AlliedFileTransfer, self).__init__(ssh_conn=ssh_conn,
                                                        source_file=source_file,
                                                        dest_file=dest_file,
                                                        file_system=file_system,
                                                        direction=direction)

    @staticmethod
    def available_space_to_bytes(available_space):
        space = None
        if available_space.endswith('K'):
            space = int(available_space[:-3])
            space = space * 1024
        elif available_space.endswith('M'):
            space = int(available_space[:-3])
            space = space * 1048576
        return space

    def remote_file_size(self, remote_cmd="", remote_file=None):
        """Get the file size of the remote file."""
        if remote_file is None:
            if self.direction == 'put':
                remote_file = self.dest_file
            elif self.direction == 'get':
                remote_file = self.source_file
        if not remote_cmd:
            remote_cmd = "dir {}/{}".format(self.file_system, remote_file)
        remote_out = self.ssh_ctl_chan.send_command(remote_cmd)
        # Strip out "Directory of flash:/filename line
        remote_out = "".join(remote_out)
        # Match line containing file name
        # Format will be 561 -rw- Jun 20 2017 22:51:49  flash:/filename
        file_size = remote_out.split()[0]
        if 'Error opening' in remote_out or 'No such file or directory' in remote_out:
            raise IOError("Unable to find file on remote system")
        else:
            return int(file_size)

    def remote_space_available(self, search_pattern=r"[0-9]+\.[0-9]."):
        """Return space available on remote device."""
        search_pattern = r"[0-9]+\.[0-9]."
        remote_cmd = "show file systems | include {}".format(self.file_system)
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        match = re.search(search_pattern, remote_output)
        available_space = match.group(0)
        return self.available_space_to_bytes(available_space)

    def verify_space_available(self, search_pattern=r"[0-9]+\.[0-9]."):
        """Verify sufficient space is available on destination file system (return boolean)."""
        if self.direction == 'put':
            space_avail = self.remote_space_available(search_pattern=search_pattern)
        elif self.direction == 'get':
            space_avail = self.local_space_available()
        if space_avail > self.file_size:
            return True
        return False

    def check_file_exists(self, remote_cmd=""):
        """Check if the dest_file already exists on the file system (return boolean)."""
        if self.direction == 'put':
            if not remote_cmd:
                remote_cmd = "dir {}/{}".format(self.file_system, self.dest_file)
            remote_out = self.ssh_ctl_chan.send_command_expect(remote_cmd)
            search_string = r"[0-9]+\:[0-9]+.*{0}".format(self.dest_file)
            if 'Error opening' in remote_out or 'No such file or directory' in remote_out:
                return False
            elif re.search(search_string, remote_out, flags=re.DOTALL):
                return True
            else:
                raise ValueError("Unexpected output from check_file_exists")
        elif self.direction == 'get':
            return os.path.exists(self.dest_file)

    def remote_md5(self, base_cmd='', remote_file=None):
        pass
