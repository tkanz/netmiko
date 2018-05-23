from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection
from netmiko.scp_handler import BaseFileTransfer


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
    def __init__(self, ssh_conn, source_file, dest_file, file_system="flash:", direction='put'):
        return super(AlliedFileTransfer, self).__init__(ssh_conn=ssh_conn,
                                                        source_file=source_file,
                                                        dest_file=dest_file,
                                                        file_system=file_system,
                                                        direction=direction)

    @staticmethod
    def available_space_to_bytes(available_space):
        space = None
        if available_space.endswith('K'):
            space = int(available_space[:-1])
            space = space * 1024
        elif available_space.endswith('M'):
            space = int(available_space[:-1])
            space = space * 1048576
        return space

    def remote_space_available(self, search_pattern=r"[0-9]+\.[0-9]."):
        """Return space available on remote device."""
        remote_cmd = "show file systems | include {}".format(self.file_system)
        remote_output = self.ssh_ctl_chan.send_command_expect(remote_cmd)
        available_space = re.search(search_pattern, remote_output)
        return self.available_space_to_bytes(available_space)

    def check_file_exists(self, remote_cmd="dir {} | include {}"):
        """Check if the dest_file already exists on the file system (return boolean)."""
        return self.check_file_exists(remote_cmd=remote_cmd.format(self.file_system, self.dest_file))
