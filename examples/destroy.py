from cloudbridge.factory import CloudProviderFactory, ProviderList
from cloudbridge.interfaces.resources import TrafficDirection
from decouple import config
import os
from cloudbridge.interfaces import InstanceState

config = {'azure_subscription_id': config('azure_subscription_id'),
          'azure_client_id': config('azure_client_id'),
          'azure_secret': config('azure_secret'),
          'azure_tenant': config('azure_tenant'),
          'azure_zone_name': config('azure_zone_name'),
          'azure_resource_group': 'cloudbridge-rg'}

provider = CloudProviderFactory().create_provider(ProviderList.AZURE, config)

kp = provider.security.key_pairs.find(name='cb-keypair')[0]

net_list = provider.networking.networks.find(label='cb-network')
net = net_list[0]

# Known network
sn_list = provider.networking.subnets.find(network=net.id,
                                           label='cb-subnet')
sn = sn_list[0]

# Router
router_list = provider.networking.routers.find(label='cb-router')
router = router_list[0]

# Gateway
gateway = net.gateways.get_or_create()

fw_list = provider.security.vm_firewalls.find(label='cb-firewall')
fw = fw_list[0]

inst_list = provider.compute.instances.find(label='cb-instance')
inst = inst_list[0]

inst.delete()
inst.wait_for([InstanceState.DELETED, InstanceState.UNKNOWN],
               terminal_states=[InstanceState.ERROR])  # Blocking call

fw.delete()
kp.delete()
os.remove('cloudbridge_intro.pem')
router.detach_gateway(gateway)
router.detach_subnet(sn)
gateway.delete()
router.delete()
sn.delete()
net.delete()