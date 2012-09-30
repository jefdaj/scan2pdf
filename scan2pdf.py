#!/usr/bin/python3

import os
import sys
import subprocess
from glob import glob
from string import ascii_lowercase
import random
import argparse
import tempfile

def run(cmd, **args):
    'runs a command and reports any errors'
    if args['verbose']:
        print(' '.join(cmd))
        subprocess.check_call(cmd)
    else:
        with open('/dev/null', 'wb') as null:
            subprocess.check_call(cmd, stdout=null, stderr=null)

def prefix(length=6):
    'generates a unique prefix for temp files'
    script = sys.argv[0]
    script = os.path.basename(script)
    script = os.path.splitext(script)[0]
    prefix = [random.choice(ascii_lowercase) for n in range(length)]
    prefix = ''.join(prefix)
    return '%s_%s' % (script, prefix)

def path(prefix, suffix='*', page=None, side=None,
         directory=tempfile.gettempdir()):
    'generates a filename with the given characteristics'
    path = [os.path.join(directory, prefix)]
    if page is not None:
        path += '%.2d' % page
    if side is not None:
        path += side
    if suffix is not None:
        path += suffix
    return ''.join(path)

def chain(*commands, **args):
    'chains commands together using temp file prefixes'
    pres = [prefix() for n in range( len(commands)-1 )]
    try:
        commands[0](pres[0], **args)
        for n in range(1, len(commands)-1):
            commands[n](pres[n-1], pres[n], **args)
        commands[-1](pres[-1], **args)
    except:
        raise
    finally:
        rm(pres, **args)

def mv(in_prefix, **args):
    'moves the finished pdf to the current directory'
    in_filenames = glob(path(in_prefix))
    out_filename = path(args['name'], suffix='.pdf', directory='.')
    assert len(in_filenames) == 1
    cmd = ['mv'] + in_filenames + [out_filename]
    run(cmd, **args)

def rm(prefixes, **args):
    'deletes temp files starting with any of the prefixes'
    cmd = ['rm']
    for prefix in prefixes:
        pattern = path(prefix)
        cmd += glob(pattern)
    run(cmd, **args)
 
def xdg_open(**args):
    'opens the finished pdf'
    if not args['open']:
        return
    filename = path(args['name'], suffix='.pdf', directory='.')
    cmd = ['xdg-open', filename]
    run(cmd, **args)

def scanimage(prefix, suffix='', reverse=False, **args):
    'scans images into tiff files in the current folder'
    if args['duplex']:
        # scan twice, naming files so they alternate
        args['duplex'] = False
        scanimage(prefix, suffix='a', reverse=False, **args)
        input('Put papers in upside down and press ENTER')
        pattern = path(prefix, '*.tif')
        args['pages'] = len(glob(pattern))
        scanimage(prefix, suffix='b', reverse=True, **args)
    else:
        # scan once
        pattern = '%%02d%s.tif' % suffix
        filename = path(prefix, pattern)
        cmd = [ 'scanimage'
              , '-x', str(args['width'])
              , '-y', str(args['height'])
              , '--batch=%s' % filename
              , '--source=%s' % args['source']
              , '--format=tiff'
              , '--resolution', '%s' % args['resolution']
              , '--batch-count=%s'   % args['pages']
              , '--mode', args['mode']
              ]
        if reverse:
            cmd += ['--batch-start', str(args['pages'])]
            cmd += ['--batch-increment', '-1']
        if args['verbose']:
            cmd.append('--progress')
        try:
            run(cmd, **args)
        except subprocess.CalledProcessError as e:
            if args['pages'] == -1 and e.returncode == 7:
                # ADF out of paper
                return
            else:
                print(e)
                raise

def convert(in_prefix, out_prefix, **args):
    'makes some minor image quality enhancements'
    pattern = path(in_prefix, '*.tif')
    for filename in glob(pattern):
        cmd = [ 'convert'
              , filename
              , '-level', '15%,85%'
              , '-depth', '2'
              , filename.replace(in_prefix, out_prefix)
              ]
        #if rotate:
        #    cmd += ['-rotate', '180']
        run(cmd, **args)

def tiffcp(in_prefix, out_prefix, **args):
    'combines multiple tiff files into one'
    cmd = ['tiffcp']
    pattern = path(in_prefix, '*.tif')
    filenames = glob(pattern)
    filenames.sort()
    cmd += filenames
    pattern2 = path(out_prefix, '.tif')
    cmd.append(pattern2)
    try:
        run(cmd, **args)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return
        else:
            raise

def tiff2pdf(in_prefix, out_prefix, **args):
    'converts a tiff file to pdf'
    src = path(in_prefix, '.tif')
    dst = path(out_prefix, '.pdf')
    cmd = [ 'tiff2pdf'
          , '-z'
          , '-o', dst
          , src
          ]
    run(cmd, **args)

def pdfsandwich(in_prefix, out_prefix, **args):
    'adds a searchable text layer to a pdf'

    # note existing temp files
    start  = glob(path('cuneiform'))
    start += glob(path('pdfsandwich'))

    # run pdfsandwich
    in_filename  = path(in_prefix,  '.pdf')
    out_filename = path(out_prefix, '.pdf')
    resolution = '%sx%s' % (args['resolution'], args['resolution'])
    cmd = [ 'pdfsandwich', in_filename , '-o', out_filename
          , '-resolution', resolution
          , '-quiet'
          ]
    if args['mode'] == 'color':
        cmd.append('-rgb')
    run(cmd, **args)

    # delete any new temp files
    end  = glob(path('cuneiform'))
    end += glob(path('pdfsandwich'))
    diff = [f for f in end if not f in start]
    if len(diff) > 0:
        cmd = ['rm', '-r'] + diff
        run(cmd, **args)

def available(prefix='scan', num=1):
    'generates an available filename starting with the prefix'
    candidate = path(prefix, suffix=None, page=num, directory='.')
    if len(glob('%s*' % candidate)) == 0:
        return candidate
    else:
        return available(prefix, num+1)

def parse(given):
    'parses command line argments into a dict'
    expected = \
        [ ('-n', '--name'      , {'default':'scan'         })
        , ('-s', '--source'    , {'default':'ADF'          })
        , ('-m', '--mode'      , {'default':'color'        })
        , ('-d', '--duplex'    , {'action':'store_true'    })
        , ('-v', '--verbose'   , {'action':'store_true'    })
        , ('-o', '--open'      , {'action':'store_true'    })
        , ('-p', '--pages'     , {'type':int, 'default': -1})
        , ('-r', '--resolution', {'type':int, 'default':300})
        , ('-x', '--width'     , {'type':int, 'default':215})
        , ('-y', '--height'    , {'type':int, 'default':275})
        ]
    parser = argparse.ArgumentParser()
    for arg in expected:
        parser.add_argument(*arg[:-1], **arg[-1])
    parsed = parser.parse_args(given)
    parsed.name = available(parsed.name)
    return parsed.__dict__

# TODO reasonable variable, function names
# TODO rewrite the path and available fns so they make sense
# TODO comments
# TODO rotate images
# TODO remove blank pages
# TODO get it to work without explicit number of pages
# TODO mv leaves old file behind (only when unnamed?)
# TODO logical sections: meta, pipeline, interface

if __name__ == '__main__':
    cmds = \
        [ scanimage
        , convert
        , tiffcp
        , tiff2pdf
        , pdfsandwich
        , mv
        ]
    args = parse(sys.argv[1:])
    chain(*cmds, **args)
    xdg_open(**args)
