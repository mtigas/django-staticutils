# staticutils

Some useful additions to `django.contrib.staticfiles`, for real-world app
development.

Currently provides:

* The ability to "version" static resources via a file MD5 hash.
  * Commands: `hashstatic`, `clearhashedstatic`, and modifications to the
    existing `collectstatic`.
  * See **Static File Versioning** section below.

## Static File Versioning

In a nutshell: allows you to set a far-future "Expires" header on all your
static files, since every static file will get a "version tag" (part of the
file's MD5 hash) added to the filename.

Why? Best practices say that you should set a far-future "Expires" header on
all your non-dynamic files, so that browsers (and proxies and CDNs) can cache
them for better performance and less overall bandwidth usage. (See
[this Yahoo Best Practices document][Yexpires].)

For more information, on this implementation see the "{% hashedstatic %}
template tag" section below.

[Yexpires]: http://developer.yahoo.com/performance/rules.html#expires

### Quick example

* Replace every instance of `{{ STATIC_URL }}foo/bar.css` (i.e. any use of
  static assets in all templates) with the template tag
  `{% hashedstatic "foo/bar.css" %}`. (Replace "`foo/bar.css`" with your actual
  static asset paths.)

When deploying your static assets, you would previously perform:

    django-admin.py collectstatic

Now you should perform:

    django-admin.py hashstatic
    django-admin.py collectstatic

If you want to be totally under the hashed-asset system you'd do this instead:

    django-admin.py clearhashedstatic #removes old files so this deploy is only the latest
    django-admin.py hashstatic --link #symlink, not copy, source files
    django-admin.py collectstatic --hashed-only

---

### {% hashedstatic %} template tag

Replaces the `{{ STATIC_URL }}foo/bar.css` paradigm in templates.

Given `{% hashedstatic "foo/bar.css" %}`, the hashed version of the given
static asset is returned instead, with `STATIC_URL` prepended, i.e.
`/statics/foo/bar.a8d2bd908f64.css`.

### hashstatic command

"Collects" static files (the same way `collectstatic` would) into the
filesystem at `HASHED_STATIC_ROOT`. Each filename gets a hash added, before
the file extension (i.e. `foo/bar.css` -> `foo/bar.a8d2bd908f64.css`).

Similar to `collectstatic`, the `--link` option simply turns the hash filename
at `HASHED_STATIC_ROOT` into a symlink to the original (wherever it may be).
This is useful if you want to use `collectstatic` to deploy these resources
where they may later be cached (to a secondary webserver, S3/CloudFront or
similar CDN, etc.) This *is* the intended usecase.

By default (i.e. without `--link`), this command makes a copy of every static
asset.

Usage:

    hashstatic [options]

    Collect static files from apps and other locations into the
    `HASHED_STATIC_ROOT` defined in settings, and adds a hash to each
    filename. (Used in conjunction with the {% cachebust %} template tag to
    map filenames to hashed filenames in templates.)

      -l, --link            Create a symbolic link to each file instead of
                            copying.

### clearhashedstatic command

Usage:

    clearhashedstatic [options]

    Purges *old* hashed static files from `HASHED_STATIC_ROOT`. Files
    where the hash in the filename matches the source file's current MD5
    hash are not removed, unless the `--all` flag is given.

      --all                 Removes everything from `HASHED_STATIC_ROOT`.
      --noinput             Does not prompt 

### collectstatic command

Modified to include `HASHED_STATIC_ROOT` in addition to `STATICFILES_DIRS`
(and app directories).

New options:

* `--hashed-only` only deploys static assetss from `HASHED_STATIC_ROOT`.
* `--plain` is the original Django behavior, ignoring `HASHED_STATIC_ROOT`.

Usage:

    collectstatic [options]

    Collect static files from apps and other locations in a single location.

      --noinput             Do NOT prompt the user for input of any kind.
      -i PATTERN, --ignore=PATTERN
                            Ignore files or directories matching this glob-style
                            pattern. Use multiple times to ignore more.
      -n, --dry-run         Do everything except modify the filesystem.
      -l, --link            Create a symbolic link to each file instead of
                            copying.
      --no-default-ignore   Don't ignore the common private glob-style patterns
                            'CVS', '.*' and '*~'.



