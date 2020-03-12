# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
#
# Copyright: 2019-2020 Red Hat Inc.
# Authors : Beraldo Leal <bleal@redhat.com>

"""
This module provides an useful API for hosts in a network.
"""

from ..ssh import Session

from .common import run_command
from .interfaces import NetworkInterface
from .exceptions import NWException


class Host:
    """This class represents a base Host and shouldn't be instantiated.

    Use one of the child classes (LocalHost or RemoteHost).

    During the initialization of a child, all interfaces will be detected and
    available via `interfaces` attribute. This could be accessed on LocalHost
    and RemoteHost instances.

    So, for instance, you could have a local and a remote host::

        remote = RemoteHost(host='foo', port=22,
                            username='foo', password='bar')
        local = LocalHost()

    You can iterate over the network interfaces of any host::

        for i in remote.interfaces:
            print(i.name, i.is_link_up())
    """
    def __init__(self, host):
        if type(self) == Host:
            raise TypeError("Host class should not be instantiated")
        self.host = host

    @property
    def interfaces(self):
        cmd = 'ls /sys/class/net'
        try:
            names = run_command(cmd, self).split()
        except Exception as ex:
            raise NWException("Failed to get interfaces: {}".format(ex))

        return [NetworkInterface(if_name=name, host=self) for name in names]

    def get_interface_by_ipaddr(self, ipaddr):
        """Return an interface that has a specific ipaddr."""
        for interface in self.interfaces:
            if ipaddr in interface.get_ipaddrs():
                return interface


class LocalHost(Host):
    """
    This class represents a local host and inherit from `Host`.

    You should use this class when trying to get information about your
    localhost.

    Example:

        local = LocalHost()
    """
    def __init__(self, host='localhost'):
        super().__init__(host)


class RemoteHost(Host):
    """
    This class represents a remote host and inherit from `Host`.

    You must provide at least an username to stablish a connection.

    Example with password:

        remote = RemoteHost(host='192.168.0.1',
                            port=22,
                            username='foo',
                            password='bar')

    You can also provide a key instead of a password.
    """
    def __init__(self, host, username, port=22, key=None, password=None):
        super().__init__(host)
        self.port = port
        self.username = username
        self.key = key
        self.password = password
        self.remote_session = self._connect()

    def _connect(self):
        session = Session(host=self.host,
                          port=self.port,
                          user=self.username,
                          key=self.key,
                          password=self.password)
        if session.connect():
            return session
        msg = "Failed connecting {}:{}".format(self.host,
                                               self.port)
        raise NWException(msg)
