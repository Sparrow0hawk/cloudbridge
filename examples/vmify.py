from cloudbridge.factory import CloudProviderFactory, ProviderList
from cloudbridge.interfaces.resources import TrafficDirection
from decouple import config
import os

# these config settings are read in from a .env file using python-decouple module
config = {'azure_subscription_id': config('azure_subscription_id'),
          'azure_client_id': config('azure_client_id'),
          'azure_secret': config('azure_secret'),
          'azure_tenant': config('azure_tenant'),
          'azure_zone_name': config('azure_zone_name'),
          'azure_resource_group': 'cloudbridge-rg'}

provider = CloudProviderFactory().create_provider(ProviderList.AZURE, config)
image_id = 'Canonical:UbuntuServer:16.04.0-LTS:latest'  # Ubuntu 16.04


kp = provider.security.key_pairs.create('cb-keypair')
with open('cloudbridge_intro.pem', 'w') as f:
    f.write(kp.material)
os.chmod('cloudbridge_intro.pem', 0o400)

net = provider.networking.networks.create(cidr_block='10.0.0.0/16',
                                          label='cb-network')
sn = net.subnets.create(
    cidr_block='10.0.0.0/28', label='cb-subnet')
router = provider.networking.routers.create(network=net, label='cb-router')
router.attach_subnet(sn)
gateway = net.gateways.get_or_create()
router.attach_gateway(gateway)


fw = provider.security.vm_firewalls.create(
    label='cb-firewall', description='A VM firewall used by CloudBridge', network=net)
fw.rules.create(TrafficDirection.INBOUND, 'tcp', 22, 22, '0.0.0.0/0')

img = provider.compute.images.get(image_id)
vm_type = sorted([t for t in provider.compute.vm_types
                  if t.vcpus >= 2 and t.ram >= 4],
                  key=lambda x: x.vcpus*x.ram)[0]
inst = provider.compute.instances.create(
    image=img, vm_type=vm_type, label='cb-instance',
    subnet=sn, key_pair=kp, vm_firewalls=[fw],
    public_ip=True)
# Wait until ready
inst.wait_till_ready()  # This is a blocking call
# Show instance state
print(inst.state)

print(inst.public_ips)

# want to avoid the below behaviour 
#if not inst.public_ips:
#    fip = gateway.floating_ips.create()
#    inst.add_floating_ip(fip)
#    inst.refresh()

print(f"Connect to VM with command: ssh -i cloudbridge_intro.pem cbuser@{inst.public_ips[0]}")