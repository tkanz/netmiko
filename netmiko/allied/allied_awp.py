from __future__ import unicode_literals
import re
import time
from netmiko.cisco_base_connection import CiscoSSHConnection


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
