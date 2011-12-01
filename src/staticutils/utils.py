import hashlib
from staticutils.settings import STATIC_HASH_LENGTH


def file_version_hash(path, storage, hash_length=STATIC_HASH_LENGTH):
    h = hashlib.md5()
    h.update(storage.open(path, 'rb').read())
    version = '%s' % h.hexdigest()
    return version[:hash_length]


def path_to_versioned_path(path, version):
    """
    Returns a versioned filename.

    If filename has an extension, the version hash comes before the extension:

        foo.css -> foo.a8d2bd908f64.css

    If the filename does not have an extension, the version hash comes after
    the base filename:

        foo/bar -> foo/bar.a8d2bd908f64
    """
    if "." in path:
        path_a, path_b = path.rsplit('.', 1)
        return "%s.%s.%s" % (path_a, version, path_b)
    else:
        return "%s.%s" % (path, version)
