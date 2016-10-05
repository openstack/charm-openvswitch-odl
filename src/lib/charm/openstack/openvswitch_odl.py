import socket
import subprocess

import charmhelpers.core.hookenv as hookenv
import charmhelpers.contrib.network.ip as ch_ip
import charms_openstack.charm
import charms_openstack.sdn.odl as odl
import charms_openstack.sdn.ovs as ovs
import charms_openstack.devices.pci as pci


class OVSODLCharm(charms_openstack.charm.OpenStackCharm):

    # Internal name of charm + keystone endpoint
    service_name = name = 'openvswitch_odl'

    # First release supported
    release = 'liberty'

    packages = ['openvswitch-switch']

    def configure_openvswitch(self, odl_ovsdb):
        hookenv.log("Configuring OpenvSwitch with ODL OVSDB controller: %s" %
                    odl_ovsdb.connection_string())
        local_ip = ch_ip.get_address_in_network(
            self.config.get('os-data-network'),
            hookenv.unit_private_ip())
        ovs.set_config('local_ip', local_ip)
        ovs.set_config('controller-ips', odl_ovsdb.private_address(),
                       table='external_ids')
        ovs.set_config('host-id', socket.gethostname(),
                       table='external_ids')
        ovs.set_manager(odl_ovsdb.connection_string())
        hookenv.status_set('active', 'Open vSwitch configured and ready')

    def unconfigure_openvswitch(self, odl_ovsdb):
        hookenv.log("Unconfiguring OpenvSwitch")
        subprocess.check_call(['ovs-vsctl', 'del-manager'])
        bridges = subprocess.check_output(['ovs-vsctl',
                                           'list-br']).split()
        for bridge in bridges:
            subprocess.check_call(['ovs-vsctl',
                                   'del-controller', bridge])
        hookenv.status_set(
            'waiting',
            'Open vSwitch not configured with an ODL OVSDB controller')

    def configure_neutron_plugin(self, neutron_plugin):
        neutron_plugin.configure_plugin(
            plugin='ovs-odl',
            config={
                "nova-compute": {
                    "/etc/nova/nova.conf": {
                        "sections": {
                            'DEFAULT': [
                                ('firewall_driver',
                                 'nova.virt.firewall.'
                                 'NoopFirewallDriver'),
                                ('libvirt_vif_driver',
                                 'nova.virt.libvirt.vif.'
                                 'LibvirtGenericVIFDriver'),
                                ('security_group_api', 'neutron'),
                            ],
                        }
                    }
                }
            })

    def odl_node_registration(self, controller):
        """ Register node with ODL if not registered already """
        odl_conn = odl.ODLConfig(**controller.connection())
        device_name = socket.gethostname()
        if odl_conn.is_device_registered(device_name):
            hookenv.log('{} is already registered in odl'.format(device_name))
        else:
            local_ip = ch_ip.get_address_in_network(
                self.config('os-data-network'),
                hookenv.unit_private_ip())
            hookenv.log('Registering {} ({}) in odl'.format(
                        device_name, local_ip))
            odl_conn.odl_register_node(device_name, local_ip)

    def odl_register_macs(self, controller):
        """ Register local interfaces and their networks with ODL """
        hookenv.log('Looking for macs to register with networks in odl')
        odl_conn = odl.ODLConfig(**controller.connection())
        device_name = socket.gethostname()
        requested_config = pci.PCIInfo()['local_config']
        for mac in requested_config.keys():
            for requested_net in requested_config[mac]:
                net = requested_net['net']
                interface = requested_net['interface']
                if not odl_conn.is_net_device_registered(net, device_name,
                                                         interface, mac,
                                                         device_type='ovs'):
                    hookenv.log('Registering {} and {} on '
                                '{}'.format(net, interface, mac))
                    odl_conn.odl_register_macs(device_name, net, interface,
                                               mac, device_type='ovs')
                else:
                    hookenv.log('{} already registered for {} on '
                                '{}'.format(net, interface, device_name))
