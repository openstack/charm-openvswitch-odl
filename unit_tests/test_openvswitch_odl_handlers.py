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

import mock

import reactive.openvswitch_odl_handlers as handlers

import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'config.changed',
            'update-status']
        hook_set = {
            'when': {
                'configure_openvswitch': (
                    'charm.installed',
                    'ovsdb-manager.access.available',),
                'unconfigure_openvswitch': (
                    'ovs.configured',),
                'configure_neutron_plugin': (
                    'neutron-plugin.connected',),
                'odl_node_registration': (
                    'controller-api.access.available',),
                'odl_mac_registration': (
                    'controller-api.access.available',),
            },
            'when_not': {
                'unconfigure_openvswitch': (
                    'ovsdb-manager.access.available',),
            }
        }
        # test that the hooks were registered via the
        # reactive.barbican_handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestConfigureOpenvswitch(test_utils.PatchHelper):

    def test_configure_openvswitch(self):
        ovs_odl_charm = mock.MagicMock()
        self.patch_object(handlers.reactive, 'set_state')
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = ovs_odl_charm
        self.provide_charm_instance().__exit__.return_value = None

        handlers.configure_openvswitch('arg1')
        ovs_odl_charm.configure_openvswitch.assert_called_once_with(('arg1'))
        self.set_state.assert_called_once_with('ovs.configured')

    def test_unconfigure_openvswitch(self):
        ovs_odl_charm = mock.MagicMock()
        self.patch_object(handlers.reactive, 'remove_state')
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = ovs_odl_charm
        self.provide_charm_instance().__exit__.return_value = None

        handlers.unconfigure_openvswitch()
        ovs_odl_charm.unconfigure_openvswitch.assert_called_once_with(None)
        self.remove_state.assert_called_once_with('ovs.configured')

    def test_configure_neutron_plugin(self):
        ovs_odl_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = ovs_odl_charm
        self.provide_charm_instance().__exit__.return_value = None

        handlers.configure_neutron_plugin('arg1')
        ovs_odl_charm.configure_neutron_plugin.assert_called_once_with(
            ('arg1'))

    def test_odl_node_registration(self):
        ovs_odl_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = ovs_odl_charm
        self.provide_charm_instance().__exit__.return_value = None

        handlers.odl_node_registration('arg1')
        ovs_odl_charm.register_node.assert_called_once_with(('arg1'))

    def test_odl_mac_registration(self):
        ovs_odl_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = ovs_odl_charm
        self.provide_charm_instance().__exit__.return_value = None

        handlers.odl_mac_registration('arg1')
        ovs_odl_charm.register_macs.assert_called_once_with(('arg1'))
