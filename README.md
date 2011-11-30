# hashstatic

"Collects" static files (the same way `collectstatic` would) into the
filesystem at `HASHED_STATIC_ROOT`. Each filename gets a hash added, before
the file extension (i.e. `foo/bar.css` -> `foo/bar.a8d2bd908f64.css`).

Option `--link` simply turns the hash filename at `HASHED_STATIC_ROOT` into
a symlink to the original (wherever it may be). This is useful if you want to
use `collectstatic` to deploy these resources where they may later be cached
(to a secondary webserver, S3/CloudFront or similar CDN, etc.) This *is* the
intended usecase.

    hashstatic [options]

    Collect static files from apps and other locations into the
    `HASHED_STATIC_ROOT` defined in settings, and adds a hash to each
    filename. (Used in conjunction with the {% cachebust %} template tag to
    map filenames to hashed filenames in templates.)

      -l, --link            Create a symbolic link to each file instead of
                            copying.

# hashstaticclear

Purges *old* hashed static files from `HASHED_STATIC_ROOT`.

# collectstatic

Modified to include `HASHED_STATIC_ROOT` in addition to `STATICFILES_DIRS`
(and app directories).

New option `--strict` which ignores the `HASHED_STATIC_ROOT` -- i.e. brings
back the original behavior of `collectstatic`.

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



