import shade

from collections import namedtuple

from cloudmesh.api.provider import Provider as ProviderInterface
from cloudmesh.api.provider import Result

from cloudmesh.util import Dotdict

import logging
logger = logging.getLogger(__name__)


class Provider(ProviderInterface):

    def __init__(self, **kwargs):

        self._cloud = shade.openstack_cloud(**kwargs)

    def _cloud_list_to_results(self, attr, *args, **kwargs):
        values = Dotdict(getattr(self._cloud, 'list_%s' % attr)(*args, **kwargs))
        return [Result(str(value.id), value)
                for value in values]

    @property
    def name(self):
        return 'openstack'      # FIXME needs self inspection for more descriptive name

    def nodes(self):
        return self._cloud_list_to_results('servers')

    def secgroups(self):
        return self._cloud_list_to_results('security_groups')

    def flavors(self):
        return self._cloud_list_to_results('flavors')

    def images(self):
        return self._cloud_list_to_results('images')

    def addresses(self):
        return self._cloud_list_to_results('floating_ips')

    def networks(self):
        return self._cloud_list_to_results('networks')

    ################################ nodes

    def allocate_node(self, name=None, image=None, flavor=None, network=None, **kwargs):

        # Sanity check
        logger.debug('OpenStack allocate_node sanity check')
        vars = locals()
        required = ['name', 'image', 'flavor', 'network']
        for _param_name in required:
            val = vars[_param_name]
            if not val:
                msg = 'Required argument %s not specified' % _param_name
                logger.critical(msg)
                raise ValueError(msg)

        logger.info('Allocating OpenStack node with name=%s, image=%s, flavor=%s, networks=%s, %s',
                    name, image, flavor, networks, str(kwargs))

        server = self._cloud.create_server(name=name,
                                           image=image,
                                           flavor=flavor,
                                           network=network,
                                           **kwargs)

        return Result(str(server.id), Dotdict(server))


    def deallocate_node(self, ident):
        logger.info('Deallocating OpenStack node %s', ident)
        self._cloud.delete_server(ident, delete_ips=True)

    def get_node(self, ident):
        n = Dotdict(self._cloud.get_server(ident))
        return Result(str(n.id), n)

    ################################ images

    def allocate_ip(self):
        ip = self._cloud.available_floating_ip()
        return Result(str(ip.id), ip)

    def deallocate_ip(self, *args, **kwargs): raise NotImplementedError()
    def associate_ip(self, *args, **kwargs): raise NotImplementedError()
    def disassociate_ip(self, *args, **kwargs): raise NotImplementedError()
    def get_ip(self, *args, **kwargs): raise NotImplementedError()

    ################################ security groups

    def allocate_secgroup(self, *args, **kwargs): raise NotImplementedError()
    def deallocate_secgroup(self, *args, **kwargs): raise NotImplementedError()
    def modify_secgroup(self, *args, **kwargs): raise NotImplementedError()
    def get_secgroup(self, *args, **kwargs): raise NotImplementedError()

    ################################ keys

    def allocate_key(self, *args, **kwargs): raise NotImplementedError()
    def deallocate_key(self, *args, **kwargs): raise NotImplementedError()
    def modify_key(self, *args, **kwargs): raise NotImplementedError()
    def get_key(self, *args, **kwargs): raise NotImplementedError()

    ################################ images

    def allocate_image(self, *args, **kwargs): raise NotImplementedError()
    def deallocate_image(self, *args, **kwargs): raise NotImplementedError()
    def get_image(self, *args, **kwargs): raise NotImplementedError()



if __name__ == '__main__':
    from os import getenv as e
    logging.basicConfig(level='INFO')
    for name in 'requests keystoneauth'.split():
        logging.getLogger(name).setLevel('INFO')

    p = Provider()

    print p.name

    print 'Nodes'
    for r in p.nodes():
        print r, r.name
    print

    print 'Security groups'
    for r in p.secgroups():
        print r.name
    print

    print 'Flavors'
    for r in p.flavors():
        print r, r.name, r.vcpus, r.ram, r.disk
    print

    print 'Images'
    for r in p.images():
        print r, r.name
    print

    print 'Addresses'
    for r in p.addresses():
        print r.id, r.floating_ip_address, '->', r.fixed_ip_address
    print

    print 'Allocate node'
    networks = filter(lambda r: r.name.startswith(e('OS_TENANT_NAME')), p.networks())[0]
    node = p.allocate_node(name='badi-cm2test',
                           image='CC-Ubuntu14.04',
                           flavor='m1.small',
                           network=networks)
    print node, p.get_node(node.id).status
    print

    print 'IP'
    ip = p.allocate_ip()
    print ip.id, ip.floating_ip_address
    print

    print 'Deallocate node'
    p.deallocate_node(node.id)
    print
