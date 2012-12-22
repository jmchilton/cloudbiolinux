import json
import re


def build_chef_properties(env, config_file):
    """
    Build python object representation of the Chef-solo node.json file from
    node_extra.json in config dir and the fabric environment.
    """

    json_properties = _parse_json(config_file)
    # Load fabric environment properties into chef config file.
    for key, value in env.iteritems():
        # Skip invalid properties.
        if key in json_properties or not isinstance(value, str):
            continue

        if key.startswith("chef_"):
            # If a property starts with chef_ assume it is meant for chef and
            # add without this prefix. So chef_apache_dir would be available
            # as apache_dir.
            json_properties[key[len("chef_"):]] = value
        else:
            # Otherwise, allow chef to access property anyway but prefix with
            # cloudbiolinux_ so it doesn't clash with anything explicitly
            # configured for chef.
            json_properties["cloudbiolinux_%s" % key] = value
    return json_properties

# Regular expression for comments
_comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)


# http://www.lifl.fr/~riquetd/parse-a-json-file-with-comments.html
def _parse_json(filename):
    """ Parse a JSON file
        First remove comments and then use the json module package
        Comments look like :
            // ...
        or
            /*
            ...
            */
    """
    with open(filename) as f:
        content = ''.join(f.readlines())

        ## Looking for comments
        match = _comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = _comment_re.search(content)

        # Return json file
        return json.loads(content)
