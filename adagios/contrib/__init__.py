import os


def get_template_name(base_path, *args):
    """ Return a full path to a template named base_path/args[0]

    If multiple arguments are provided, treat them as recursive directories, but
    if a valid filename is found, return immediately.

    if base_path is not provided, use adagios.settings.contrib_dir
    """
    if not base_path:
        base_path = adagios.settings.contrib_dir
    path = base_path
    for i in args:
        if not i:
            continue
        path = os.path.join(path, i)
        path = os.path.normpath(path)

        if not path.startswith(base_path):
            raise Exception("'%s' is outside contrib dir" % path)
        elif os.path.isdir(path):
            continue
        elif os.path.isfile(path):
            return path
    return path
