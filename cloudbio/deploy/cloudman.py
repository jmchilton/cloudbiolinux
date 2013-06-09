import yaml
from os.path import exists, join
from fabric.api import local, lcd, env
from .util import eval_template
from tempfile import mkdtemp

DEFAULT_CLOUDMAN_PASSWORD = 'adminpass'
DEFAULT_CLOUDMAN_CLUSTER_NAME = 'cloudman'


def bundle_cloudman(options):
    cloudman_options = options.get('cloudman')
    cloudman_repository_path = cloudman_options['cloudman_repository']
    delete_repository = False
    bucket_source = cloudman_options.get("bucket_source")
    if cloudman_repository_path.startswith("http"):
        # Not a local path, lets clone it out of a remote repostiroy,
        temp_directory = mkdtemp()
        if cloudman_repository_path.endswith(".git"):
            branch_opts = ""
            repository_branch = cloudman_options.get('repository_branch', None)
            if repository_branch:
                branch_opts = "-b '%s'" % repository_branch
            clone_command = "git clone " + branch_opts + " '%s' '%s'"
        else:
            clone_command = "hg clone '%s' '%s'"
        local(clone_command % (cloudman_repository_path, temp_directory))
        cloudman_repository_path = temp_directory
        delete_repository = True
    try:
        with lcd(cloudman_repository_path):
            try:
                local("tar czvf cm.tar.gz *")
                local("mv cm.tar.gz '%s'" % bucket_source)
            finally:
                local("rm -f cm.tar.gz")
    finally:
        if delete_repository:
            local("rm -rf '%s'" % cloudman_repository_path)


def cloudman_launch(vm_launcher, options):
    cloudman_options = options.get('cloudman')
    image_id = cloudman_options.get('image_id', None)
    if str(image_id).lower() == "__use_snaps__":
        # TODO: Make more flexible
        bucket_source = cloudman_options.get("bucket_source")
        snaps_path = join(bucket_source, "snaps.yaml")
        if not exists(snaps_path):
            raise Exception("CloudMan AMI set to __use_snaps__ but now snaps.yaml file could be found with path %s" % snaps_path)
        snaps = {}
        with open(snaps_path, "r") as in_handle:
            snaps = yaml.load(in_handle)
        clouds = snaps["clouds"]
        if len(clouds) != 1:
            raise Exception("Exactly one cloud must be defined snaps.yaml for the deployer's CloudMan launch to work.")
        regions = clouds[0]["regions"]
        if len(regions) != 1:
            raise Exception("Exactly one region must be defined snaps.yaml for the deployer's CloudMan launch to work.")
        deployments = regions[0]["deployments"]
        if len(deployments) != 1:
            raise Exception("Exactly one deployment must be defined snaps.yaml for the deployer's CloudMan launch to work.")
        image_id = deployments[0]["default_mi"]

    size_id = cloudman_options.get('size_id', None)
    user_data = _prepare_user_data(vm_launcher, options)
    vm_launcher.create_node('cloudman',
                            image_id=image_id,
                            size_id=size_id,
                            ex_userdata=user_data)


def _prepare_user_data(vm_launcher, options):
    cloudman_options = options.get('cloudman')
    cloudman_user_data = cloudman_options.get('user_data', {})
    cluster_name = \
        cloudman_options.get('cluster_name', DEFAULT_CLOUDMAN_CLUSTER_NAME)
    password = cloudman_options.get('password', DEFAULT_CLOUDMAN_PASSWORD)
    access_key = vm_launcher.access_id()
    secret_key = vm_launcher.secret_key()

    _set_property_if_needed(cloudman_user_data, 'access_key', access_key)
    _set_property_if_needed(cloudman_user_data, 'secret_key', secret_key)
    cluster_name = eval_template(env, cluster_name)
    _set_property_if_needed(cloudman_user_data, 'cluster_name', cluster_name)
    _set_property_if_needed(cloudman_user_data, 'password', password)

    if not options.get("skip_cloudman", False):
        cloudman_user_data["skip_cloudman"] = True

    return yaml.dump(cloudman_user_data)


def _set_property_if_needed(user_data, property, value):
    if property not in user_data:
        user_data[property] = value
