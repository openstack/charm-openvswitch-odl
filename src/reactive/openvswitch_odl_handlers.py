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

import charms_openstack.charm as charm
import charms.reactive as reactive

# This charm's library contains all of the handler code associated with
# ovs_odl
import charm.openstack.openvswitch_odl as ovs_odl  # noqa

charm.use_defaults(
    'charm.installed',
    'config.changed',
    'update-status')


@reactive.when('ovsdb-manager.access.available')
@reactive.when('charm.installed')
def configure_openvswitch(odl_ovsdb):
    with charm.provide_charm_instance() as ovs_odl_charm:
        ovs_odl_charm.configure_openvswitch(odl_ovsdb)
    reactive.set_state('ovs.configured')


@reactive.when('ovs.configured')
@reactive.when_not('ovsdb-manager.access.available')
def unconfigure_openvswitch(odl_ovsdb=None):
    with charm.provide_charm_instance() as ovs_odl_charm:
        ovs_odl_charm.unconfigure_openvswitch(odl_ovsdb)
    reactive.remove_state('ovs.configured')


@reactive.when('neutron-plugin.connected')
def configure_neutron_plugin(neutron_plugin):
    with charm.provide_charm_instance() as ovs_odl_charm:
        ovs_odl_charm.configure_neutron_plugin(neutron_plugin)


@reactive.when('controller-api.access.available')
def odl_node_registration(controller):
    with charm.provide_charm_instance() as ovs_odl_charm:
        ovs_odl_charm.register_node(controller)


@reactive.when('controller-api.access.available')
def odl_mac_registration(controller):
    with charm.provide_charm_instance() as ovs_odl_charm:
        ovs_odl_charm.register_macs(controller)
