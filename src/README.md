# Overview

This subordinate charm provides OpenvSwitch integration with an OpenDayLight (ODL) controller.

Its design to support deployment of principle charms as part of an ODL SDN deployment.

It also optionally supports deployment and configuration with OpenStack Compute (Nova).

# Usage

To deploy (partial deployment only - see other charms for full details):

    juju deploy openvswitch-odl
    juju deploy odl-controller
    juju add-relation odl-controller openvswitch-odl


This charm can be used with any other principle charm:

    juju deploy ubuntu
    juju add-relation openvswitch-odl ubuntu

or with the OpenStack nova-compute and neutron-gateway charms:

    juju deploy nova-compute
    juju deploy neutron-gateway
    juju add-relation nova-compute openvswitch-odl
    juju add-relation neutron-gateway openvswitch-odl

# Configuration Options

This charm will optionally configure the local ip address of the OVS instance to something other than the 'private-address' provided by Juju:

    juju set openvswitch-odl os-data-network=10.20.3.0/21

The charm will scan configured network interfaces, and reconfigure the OVS instance with an alternative IP address if one is found within the configure subnet CIDR.

# Restrictions

This charm can't be deployed under LXC containers; however it will work just fine under KVM or on bare metal.
