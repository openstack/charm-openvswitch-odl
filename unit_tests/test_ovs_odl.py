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

import testtools

from mock import call
from mock import patch
from mock import MagicMock

import reactive.main as ovs_odl_main

TO_PATCH = [
    'get_address_in_network',
    'config',
    'log',
    'status_set',
    'unit_private_ip',
    'when',
    'when_not',
    'kv',
    'subprocess',
    'ovs',
    'gethostname',
]

CONN_STRING = 'tcp:odl-controller:6640'
LOCALHOST = '10.1.1.1'


class CharmUnitTestCase(testtools.TestCase):

    def setUp(self, obj, patches):
        super(CharmUnitTestCase, self).setUp()
        self.patches = patches
        self.obj = obj
        self.patch_all()

    def patch(self, method):
        _m = patch.object(self.obj, method)
        mock = _m.start()
        self.addCleanup(_m.stop)
        return mock

    def patch_all(self):
        for method in self.patches:
            setattr(self, method, self.patch(method))


class MockUnitData():

    data = {}

    def set(self, k, v):
        self.data[k] = v

    def unset(self, k):
        if k in self.data:
            del self.data[k]

    def get(self, k):
        return self.data.get(k)

    def reset(self):
        self.data = {}


class TestOVSODL(CharmUnitTestCase):

    def setUp(self):
        super(TestOVSODL, self).setUp(ovs_odl_main, TO_PATCH)
        self.unitdata = MockUnitData()
        self.unit_private_ip.return_value = LOCALHOST
        self.kv.return_value = self.unitdata

    def tearDown(self):
        super(TestOVSODL, self).tearDown()
        self.unitdata.reset()

    def test_configure_openvswitch_not_installed(self):
        self.unitdata.unset('installed')
        odl_ovsdb = MagicMock()
        ovs_odl_main.configure_openvswitch(odl_ovsdb)
        self.assertFalse(self.subprocess.check_call.called)

    def test_configure_openvswitch_installed(self):
        self.unitdata.set('installed', True)
        odl_ovsdb = MagicMock()
        odl_ovsdb.connection_string.return_value = None
        ovs_odl_main.configure_openvswitch(odl_ovsdb)
        self.assertFalse(self.subprocess.check_call.called)

    def test_configure_openvswitch_installed_related(self):
        self.unitdata.set('installed', True)
        self.gethostname.return_value = 'ovs-host'
        self.subprocess.check_output.return_value = 'local_uuid'
        self.config.return_value = None
        self.get_address_in_network.return_value = LOCALHOST
        odl_ovsdb = MagicMock()
        odl_ovsdb.connection_string.return_value = CONN_STRING
        odl_ovsdb.private_address.return_value = 'odl-controller'
        ovs_odl_main.configure_openvswitch(odl_ovsdb)
        self.ovs.set_manager.assert_called_with(CONN_STRING)
        self.ovs.set_config.assert_has_calls([
            call('local_ip', '10.1.1.1'),
            call('controller-ips', 'odl-controller',
                 table='external_ids'),
            call('host-id', 'ovs-host',
                 table='external_ids'),
        ])
        self.get_address_in_network.assert_called_with(None, '10.1.1.1')
        self.status_set.assert_called_with('active',
                                           'Open vSwitch configured and ready')

    def test_unconfigure_openvswitch_not_installed(self):
        self.unitdata.unset('installed')
        odl_ovsdb = MagicMock()
        ovs_odl_main.unconfigure_openvswitch(odl_ovsdb)
        self.assertFalse(self.subprocess.check_call.called)

    def test_unconfigure_openvswitch_installed(self):
        self.unitdata.set('installed', True)
        self.subprocess.check_output.return_value = 'br-int br-ex'
        odl_ovsdb = MagicMock()
        ovs_odl_main.unconfigure_openvswitch(odl_ovsdb)
        self.subprocess.check_call.assert_has_calls([
            call(['ovs-vsctl', 'del-manager']),
            call(['ovs-vsctl', 'del-controller', 'br-int']),
            call(['ovs-vsctl', 'del-controller', 'br-ex']),
        ])

    def test_configure_neutron_plugin(self):
        neutron_plugin = MagicMock()
        ovs_odl_main.configure_neutron_plugin(neutron_plugin)
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
