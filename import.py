#!/usr/bin/env python

import os
import re
import sys
import exif
import time
import hashlib

from glob import iglob
from itertools import (
    chain,
    count,
)

def join_path(*args):
    return os.path.normpath(os.path.join(*args))

def convert_mtime(m):
    """
    >>> convert_mtime(1341442601)
    '20120704185641'
    """
    return time.strftime('%Y%m%d%H%M%S', time.localtime(m))


def convert_exif_datetime_string(s):
    """
    >>> convert_exif_datetime_string(None)
    Traceback (most recent call last):
        ...
    AssertionError
    >>> convert_exif_datetime_string('2012:07:04 18:56')
    Traceback (most recent call last):
        ...
    AssertionError: 2012:07:04 18:56

    >>> convert_exif_datetime_string('2012:07:04 18:56:41:00')
    Traceback (most recent call last):
        ...
    AssertionError: 2012:07:04 18:56:41:00

    >>> convert_exif_datetime_string('2012:07:04 18:56:41')
    '20120704185641'
    """
    # Sample value:
    # In [46]: tags['Image DateTime'].printable
    # Out[46]: '2012:07:04 18:56:41'
    assert s, s
    assert s.count(' ') == 1, s
    assert s.count(':') == 4, s
    return s.replace(':', '').replace(' ', '')


def main():

    abspath = os.path.abspath(__file__)
    basedir = os.path.dirname(abspath)
    assert os.getcwd() == basedir, "%s != %s" % (os.getcwd(), basedir)

    if 'doctest' in sys.argv:
        import doctest
        doctest.testmod()
        return

    photos = re.compile('.+(\.jpg|\.jpeg|\.png)$')
    movies = re.compile('.+(\.mpg|\.mpeg|\.mov|\.avi)$')
    ignore = re.compile('.+\.py[c]?$')
    w = sys.stdout.write
    for f in iglob('*.*'):
        if ignore.match(f):
            continue

        lower = f.lower()
        is_photo = bool(photos.match(lower))
        is_movie = bool(movies.match(lower))
        if not (is_movie or is_photo):
            w("%s: not a photo or movie, skipping...\n" % f)
            continue

        # On UNIX (at least on OS X where this was first written), mtime
        # is more likely to represent the time the image was created versus
        # ctime if the image has just been imported.  However, if we may
        # import old photos that lived on Windows drives for a while, where
        # ctime may be more accurate.  Basically, pick the earliest one.
        # (Which we then simply refer to as ``mtime``.  Despite it actually
        # representing ctime.  Heh.)
        s = os.stat(f)
        mtime = s.st_mtime
        if s.st_ctime < s.st_mtime:
            w("%s: ctime < mtime: %s < %s\n" % (f, s.st_ctime, s.st_mtime))
            mtime = s.st_ctime

        mtime = convert_mtime(mtime)

        data = None
        exif_time = mtime
        with open(f, 'r') as h:
            data = h.read()
            h.seek(0)
            if is_photo:
                try:
                    tags = exif.process_file(h)
                    exif_time_str = tags['Image DateTime'].printable
                    exif_time = convert_exif_datetime_string(exif_time_str)
                except KeyError:
                    pass

        timestr = None
        if exif_time == mtime:
            timestr = exif_time
        else:
            if '--use-exif' in sys.argv:
                timestr = exif_time
            elif '--use-mtime' in sys.argv:
                timestr = mtime
            else:
                args = (f, exif_time, mtime)
                w("%s: exif/mtime mismatch: %s != %s\n" % args)
                continue

        assert timestr

        year = timestr[0:4]
        if not os.path.isdir(year):
            os.makedirs(year)
        assert os.path.isdir(year)


        # .jpeg->.jpg && .mpeg->.mpg
        ending = lower[f.rfind('.'):].replace('peg', 'pg')

        # Make sure the new file name is unique.
        need_to_rename_original = False
        for i in chain(('',), count(2)):
            name = ''.join((timestr, ('-' if i else ''), str(i), ending))
            path = join_path(basedir, year, name)
            if os.path.exists(path):
                our_cxsum = hashlib.sha256(data).hexdigest()
                with open(path, 'r') as t:
                    their_cxsum = hashlib.sha256(t.read()).hexdigest()

                if our_cxsum == their_cxsum:
                    args = (f, year, name)
                    w('%s identical to %s/%s, skipping...\n' % args)
                    name = None
                    break

                if not i:
                    need_to_rename_original = True

            if not os.path.exists(path):
                break

        if not name:
            continue

        if need_to_rename_original:
            original_name = timestr + ending
            original_path = join_path(basedir, year, original_name)
            new_name = timestr + '-1' + ending
            new_path = join_path(basedir, year, new_name)
            msg = "%s: %s, %s" % (f, original_path, new_path)
            assert not os.path.exists(new_path), msg
            w('%s/%s -> %s/%s\n' % args)
            os.rename(original_path, new_path)

        w('%s -> %s/%s' % (f, year, name))

        os.rename(os.path.abspath(f), path)

        w('\n')

if __name__ == '__main__':
    main()

# vim:set ts=8 sw=4 sts=4 tw=78 et:
