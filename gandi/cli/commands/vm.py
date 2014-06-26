
import click

from gandi.cli.core.cli import cli
from gandi.cli.core.utils import (
    output_vm, output_image, output_generic,
)
from gandi.cli.core.params import (
    pass_gandi, option, IntChoice, DATACENTER, DISK_IMAGE,
)


@cli.command()
@click.option('--state', default=None, help='filter results by state')
@click.option('--id', help='display ids', is_flag=True)
@pass_gandi
def list(gandi, state, id):
    """List virtual machines."""

    options = {}
    if state:
        options['state'] = state

    output_keys = ['hostname', 'state']
    if id:
        output_keys.append('id')

    datacenters = gandi.datacenter.list()
    result = gandi.iaas.list(options)
    for vm in result:
        gandi.echo('-' * 10)
        output_vm(gandi, vm, datacenters, output_keys)

    return result


@cli.command()
@click.argument('resource', nargs=-1)
@pass_gandi
def info(gandi, resource):
    """Display information about a virtual machine.

    Resource can be a Hostname or an ID
    """

    output_keys = ['hostname', 'state', 'cores', 'memory', 'console',
                   'datacenter', 'ip']

    datacenters = gandi.datacenter.list()
    ret = []
    for item in resource:
        vm = gandi.iaas.info(item)
        output_vm(gandi, vm, datacenters, output_keys, 14)
        ret.append(vm)
        for disk in vm['disks']:
            disk_out_keys = ['label', 'kernel_version', 'name', 'size']
            output_image(gandi, disk, datacenters, disk_out_keys, 14)

    return ret


@cli.command()
@click.argument('resource', nargs=-1)
@click.option('--background', default=False, is_flag=True,
              help='run in background mode (default=False)')
@pass_gandi
def stop(gandi, background, resource):
    """Stop a virtual machine.

    Resource can be a Hostname or an ID
    """

    output_keys = ['id', 'type', 'step']

    opers = gandi.iaas.stop(resource, background)
    if background:
        for oper in opers:
            output_generic(gandi, oper, output_keys)

    return opers


@cli.command()
@click.argument('resource', nargs=-1)
@click.option('--background', default=False, is_flag=True,
              help='run in background mode (default=False)')
@pass_gandi
def start(gandi, background, resource):
    """Start a virtual machine.

    Resource can be a Hostname or an ID
    """

    output_keys = ['id', 'type', 'step']

    opers = gandi.iaas.start(resource, background)
    if background:
        for oper in opers:
            output_generic(gandi, oper, output_keys)

    return opers


@cli.command()
@click.argument('resource', nargs=-1)
@click.option('--background', default=False, is_flag=True,
              help='run in background mode (default=False)')
@pass_gandi
def reboot(gandi, background, resource):
    """Reboot a virtual machine.

    Resource can be a Hostname or an ID
    """

    output_keys = ['id', 'type', 'step']

    opers = gandi.iaas.reboot(resource, background)
    if background:
        for oper in opers:
            output_generic(gandi, oper, output_keys)

    return opers


@cli.command()
@click.option('--background', default=False, is_flag=True,
              help='run in background mode (default=False)')
@click.argument('resource', nargs=-1)
@pass_gandi
def delete(gandi, resource, background):
    """Delete a virtual machine.

    Resource can be a Hostname or an ID
    """

    output_keys = ['id', 'type', 'step']

    stop_opers = []
    for item in resource:
        vm = gandi.iaas.info(item)
        if vm['state'] == 'running':
            oper = gandi.iaas.stop(item, background)
            if not background:
                stop_opers.append(oper)

    opers = gandi.iaas.delete(resource, background)
    if background:
        for oper in stop_opers + opers:
            output_generic(gandi, oper, output_keys)

    return opers


@cli.command()
@option('--datacenter', type=DATACENTER, default='FR',
        help='datacenter where the VM will be spawned')
@option('--memory', type=click.INT, default=256,
        help='quantity of RAM in Megabytes to allocate')
@option('--cores', type=click.INT, default=1,
        help='number of cpu')
@option('--ip-version', type=IntChoice([4, 6]), default=4,
        help='version of the created IP')
@option('--bandwidth', type=click.INT, default=102400,
        help="network bandwidth in bit/s used to create the VM's first "
             "network interface")
@option('--login', default='admin',
        help='login to create on the VM')
@click.option('--password', default=False, is_flag=True,
              help='password to set to the root account and the created login')
@option('--hostname', default='tempo',
        help='hostname of the VM')
@option('--image', type=DISK_IMAGE, default='Debian 7',
        help='disk image used to boot the vm')
@click.option('--run', default=None,
              help='shell command that will run at the first startup of a VM.'
                   'This command will run with root privileges in the ``/`` '
                   'directory at the end of its boot: network interfaces and '
                   'disks are mounted')
@click.option('--background', default=False, is_flag=True,
              help='run creation in background mode (default=False)')
@click.option('--ssh-key', default=None,
              help='Authorize ssh authentication for the given ssh key')
@pass_gandi
def create(gandi, datacenter, memory, cores, ip_version, bandwidth, login,
           password, hostname, image, run, background, ssh_key):
    """Create a new virtual machine.

    you can specify a configuration entry named 'ssh_key' containing
    path to your ssh_key file

    >>> gandi config -g ssh_key ~/.ssh/id_rsa.pub

    to know which disk image label (or id) to use as image

    >>> gandi images

    """
    pwd = None
    if password:
        pwd = click.prompt('password', hide_input=True,
                           confirmation_prompt=True)

    result = gandi.iaas.create(datacenter, memory, cores, ip_version,
                               bandwidth, login, pwd, hostname,
                               image, run,
                               background, ssh_key)
    if background:
        gandi.pretty_echo(result)

    return result


@cli.command()
@click.option('--memory', type=click.INT, default=None,
              help='quantity of RAM in Megabytes to allocate')
@click.option('--cores', type=click.INT, default=None,
              help='number of cpu')
@click.option('--console', default=None, is_flag=True,
              help='activate the emergency console')
@click.option('--background', default=False, is_flag=True,
              help='run creation in background mode (default=False)')
@click.argument('resource')
@pass_gandi
def update(gandi, resource, memory, cores, console, background):
    """Update a virtual machine.

    Resource can be a Hostname or an ID
    """

    result = gandi.iaas.update(resource, memory, cores, console, background)
    if background:
        gandi.pretty_echo(result)

    return result


@cli.command()
@click.argument('resource')
@pass_gandi
def console(gandi, resource):
    """Open a console to virtual machine.

    Resource can be a Hostname or an ID
    """

    gandi.iaas.console(resource)


@cli.command()
@click.option('--datacenter', type=DATACENTER, default=None,
              help='filter by datacenter')
@click.argument('label', required=False)
@pass_gandi
def images(gandi, label, datacenter):
    """List available system images for virtual machines.

    You can also filter results using label, by example:

    >>> gandi vm images Ubuntu --datacenter FR

    or

    >>> gandi vm images 'Ubuntu 10.04' --datacenter FR

    """

    output_keys = ['label', 'os_arch', 'kernel_version', 'disk_id',
                   'dc']

    datacenters = gandi.datacenter.list()
    result = gandi.image.list(datacenter, label)
    for image in result:
        gandi.echo('-' * 10)
        output_image(gandi, image, datacenters, output_keys)

    return result


@cli.command(root=True)
@click.option('--id', help='display ids', is_flag=True)
@pass_gandi
def datacenters(gandi, id):
    """List available datacenters."""

    output_keys = ['iso', 'name', 'country']
    if id:
        output_keys.append('id')

    result = gandi.datacenter.list()
    for dc in result:
        gandi.echo('-' * 10)
        output_generic(gandi, dc, output_keys)

    return result