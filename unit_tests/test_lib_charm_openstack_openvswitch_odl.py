# Copyright 2016 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import print_function

import unittest

import mock

import charm.openstack.openvswitch_odl as openvswitch_odl

CONN_STRING = 'tcp:odl-controller:6640'
LOCALHOST = '10.1.1.1'


class Helper(unittest.TestCase):

    def setUp(self):
        self._patches = {}
        self._patches_start = {}

    def tearDown(self):
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch(self, obj, attr, return_value=None, **kwargs):
        mocked = mock.patch.object(obj, attr, **kwargs)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)


class TestOpenStackOVSODLCharm(Helper):

    def test_configure_openvswitch(self):
        odl_ovsdb = mock.MagicMock()
        self.patch(openvswitch_odl.ch_ip, 'get_address_in_network')
        self.patch(openvswitch_odl.hookenv, 'log')
        self.patch(openvswitch_odl.hookenv, 'status_set')
        self.patch(openvswitch_odl.hookenv, 'unit_private_ip')
        self.patch(openvswitch_odl.ovs, 'set_config')
        self.patch(openvswitch_odl.ovs, 'set_manager')
        self.patch(openvswitch_odl.socket, 'gethostname')
        self.gethostname.return_value = 'ovs-host'
        self.unit_private_ip.return_value = LOCALHOST
        self.get_address_in_network.return_value = LOCALHOST
        odl_ovsdb.connection_string.return_value = CONN_STRING
        odl_ovsdb.private_address.return_value = 'odl-controller'
        a = openvswitch_odl.OVSODLCharm()
        a.configure_openvswitch(odl_ovsdb)
        self.set_manager.assert_called_with(CONN_STRING)
        self.set_config.assert_has_calls([
            mock.call('local_ip', '10.1.1.1'),
            mock.call('controller-ips', 'odl-controller',
                      table='external_ids'),
            mock.call('host-id', 'ovs-host',
                      table='external_ids'),
        ])
        self.get_address_in_network.assert_called_with(mock.ANY, '10.1.1.1')
        self.status_set.assert_called_with('active',
                                           'Unit is ready')

    def test_unconfigure_openvswitch(self):
        odl_ovsdb = mock.MagicMock()
        self.patch(openvswitch_odl.hookenv, 'log')
        self.patch(openvswitch_odl.hookenv, 'status_set')
        self.patch(openvswitch_odl.subprocess, 'check_call')
        self.patch(openvswitch_odl.subprocess, 'check_output')
        self.check_output.return_value = "br-data\nbr-ex\nbr-int\n"
        a = openvswitch_odl.OVSODLCharm()
        a.unconfigure_openvswitch(odl_ovsdb)
        check_call_calls = [
            mock.call(['ovs-vsctl', 'del-manager']),
            mock.call(['ovs-vsctl', 'del-controller', 'br-data']),
            mock.call(['ovs-vsctl', 'del-controller', 'br-ex']),
            mock.call(['ovs-vsctl', 'del-controller', 'br-int'])]
        self.check_call.assert_has_calls(check_call_calls)
        self.check_output.assert_called_once_with(['ovs-vsctl', 'list-br'])
        self.status_set.assert_called

    def test_configure_neutron_plugin(self):
        neutron_plugin = mock.MagicMock()
        a = openvswitch_odl.OVSODLCharm()
        a.configure_neutron_plugin(neutron_plugin)
        neutron_plugin.configure_plugin.assert_called_with(
            plugin='ovs-odl',
            config={
                "nova-compute": {
                    "/etc/nova/nova.conf": {
                        "sections": {
                            'DEFAULT': [
                                ('firewall_driver',
                                 'nova.virt.firewall.NoopFirewallDriver'),
                                ('libvirt_vif_driver',
                                 'nova.virt.libvirt.vif.'
                                 'LibvirtGenericVIFDriver'),
                                ('security_group_api', 'neutron'),
                            ],
                        }
                    }
                }
            }
        )

    def test_odl_node_registration(self):
        controller = mock.MagicMock()
        odl = mock.MagicMock()
        self.patch(openvswitch_odl.socket, 'gethostname')
        self.patch(openvswitch_odl.odl, 'ODLConfig')
        self.patch(openvswitch_odl.ch_ip, 'get_address_in_network')
        self.patch(openvswitch_odl.hookenv, 'log')
        self.patch(openvswitch_odl.hookenv, 'unit_private_ip')
        self.gethostname.return_value = 'ovs-host'
        self.unit_private_ip.return_value = LOCALHOST
        self.get_address_in_network.return_value = LOCALHOST
        self.ODLConfig.return_value = odl
        odl.is_device_registered.return_value = False
        a = openvswitch_odl.OVSODLCharm()
        a.odl_node_registration(controller)
        self.get_address_in_network.assert_called_once_with(mock.ANY,
                                                            '10.1.1.1')
        odl.odl_register_node.assert_called_once_with('ovs-host', '10.1.1.1')

    def test_odl_node_registration_already_registered(self):
        controller = mock.MagicMock()
        odl = mock.MagicMock()
        self.patch(openvswitch_odl.socket, 'gethostname')
        self.patch(openvswitch_odl.odl, 'ODLConfig')
        self.ODLConfig.return_value = odl
        odl.is_device_registered.return_value = True
        a = openvswitch_odl.OVSODLCharm()
        a.odl_node_registration(controller)
        self.assertFalse(odl.odl_register_node.called)

    def test_odl_register_macs(self):
        controller = mock.MagicMock()
        odl = mock.MagicMock()
        odl.is_net_device_registered.return_value = False
        self.patch(openvswitch_odl.socket, 'gethostname')
        self.patch(openvswitch_odl.odl, 'ODLConfig')
        self.patch(openvswitch_odl.pci, 'PCIInfo')
        self.ODLConfig.return_value = odl
        self.gethostname.return_value = 'ovs-host'
        self.PCIInfo.return_value = {
            'local_config': {
                'mac1': [
                    {'net': 'net1', 'interface': 'eth1'}]}}
        a = openvswitch_odl.OVSODLCharm()
        a.odl_register_macs(controller)
        odl.odl_register_macs.assert_called_once_with(
            'ovs-host', 'net1', 'eth1', 'mac1', device_type='ovs')
