#!/usr/bin/env python

import os
import re
import sys
import exif
import time
import stat

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
        #doctest.testfile(abspath, module_relative=False, verbose=True)
        doctest.testmod()
        return

    pattern = '.+(\.jpg|\.jpeg|\.png)$'
    expected = re.compile(pattern)
    ignore = re.compile('.+\.py[c]?$')
    w = sys.stdout.write
    for f in iglob('*.*'):
        if ignore.match(f):
            continue

        lower = f.lower()
        assert expected.match(lower), f

        with open(f, 'r') as h:
            exif_time_str = exif.process_file(h)['Image DateTime'].printable

        exif_time = convert_exif_datetime_string(exif_time_str)
        mtime = convert_mtime(os.stat(f).st_mtime)

        w(f)
        timestr = None
        if exif_time == mtime:
            timestr = exif_time
        else:
            if '--use-exif' in sys.argv:
                timestr = exif_time
            elif '--use-mtime' in sys.argv:
                timestr = mtime
            else:
                w(": exif/mtime mismatch: %s != %s\n" % (exif_time, mtime))
                continue

        assert timestr

        year = timestr[0:4]
        if not os.path.isdir(year):
            os.makedirs(year)
        assert os.path.isdir(year)


        ending = lower[f.rfind('.'):]
        if ending == '.jpeg':
            ending = '.jpg'

        # Make sure the new file name is unique.
        for i in chain(('',), count(2)):
            name = ''.join((timestr, ('-' if i else ''), str(i), ending))
            path = os.path.join(basedir, year, name)
            if not os.path.exists(path):
                break

        w(' -> %s/%s' % (year, name))

        os.rename(os.path.abspath(f), path)

        w('\n')

if __name__ == '__main__':
    main()

# vim:set ts=8 sw=4 sts=4 tw=78 et:
