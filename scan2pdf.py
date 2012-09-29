#!/usr/bin/python3

import os
import sys
import subprocess
from glob import glob
from string import ascii_lowercase
import random
import argparse
import tempfile

### files ###

def prefix(length=6):
    'generates a unique prefix for temp files'
    prefix = [random.choice(ascii_lowercase) for n in range(length)]
    return ''.join(prefix)

def path(prefix, suffix, page=None, side=None,
         directory=tempfile.gettempdir()):
    'combines path components'
    path = [os.path.join(directory, prefix)]
    if page:
        path += '%.2d' % page
    if side:
        path += side
    path += suffix
    return ''.join(path)

def name(prefix='scan', num=1):
    'finds an available filename starting with the prefix'
    candidate = path(prefix, '*', page=num)
    if len(glob(candidate)) == 0:
        return candidate
    else:
        return name(prefix, num+1)

def mv(in_prefix, **args):
    'moves the finished pdf to the current directory'
    in_filenames = glob(path(in_prefix, '*'))
    assert len(in_filenames) == 1
    out_filename = path(args['name'], '.pdf', directory='.')
    cmd = ['mv', in_filenames[0], out_filename]
    if args['verbose']:
        print(' '.join(cmd))
    subprocess.check_call(cmd)

def rm(prefixes, **args):
    'deletes temp files starting with any of the prefixes'
    cmd = ['rm']
    for prefix in prefixes:
        pattern = path(prefix, '*')
        cmd += glob(pattern)
    if args['verbose']:
        print(' '.join(cmd))
    subprocess.check_call(cmd)
 
def xdg_open(**args):
    'opens the finished pdf'
    if not args['open']:
        return
    filename = path(args['name'], '.pdf', directory='.')
    cmd = ['xdg-open', filename]
    if args['verbose']:
        print(' '.join(cmd))
    subprocess.check_call(cmd)

### scanning ###

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
            print(' '.join(cmd))
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            if args['pages'] == -1 and e.returncode == 7:
                # ADF out of paper
                return
            else:
                raise

### image processing ###

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
        if args['verbose']:
            print(' '.join(cmd))
        subprocess.check_call(cmd)

def tiffcp(in_prefix, out_prefix, **args):
    'combines multiple tiff files into one'
    cmd = ['tiffcp']
    pattern = path(in_prefix, '*.tif')
    filenames = glob(pattern)
    filenames.sort()
    cmd += filenames
    pattern2 = path(out_prefix, '.tif')
    cmd.append(pattern2)
    if args['verbose']:
        print(' '.join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return
        else:
            raise

def tiff2pdf(in_prefix, out_prefix, **args):
    'converts a tiff file to pdf'
    src = path(in_prefix, '.tif')
    #dst = path(args['name'], '.pdf', directory='.')
    dst = path(out_prefix, '.pdf')
    cmd = [ 'tiff2pdf'
          , '-z'
          , '-o', dst
          , src
          ]
    if args['verbose']:
        print(' '.join(cmd))
    subprocess.check_call(cmd)

def pdfocr(in_prefix, out_prefix, **args):
    'adds a searchable text layer to a pdf'
    in_filename  = path(in_prefix,  '.pdf')
    out_filename = path(out_prefix, '.pdf')
    cmd = [ 'pdfocr'
          , '-i', in_filename
          , '-o', out_filename
          ]
    if args['verbose']:
        print(' '.join(cmd))
    subprocess.check_call(cmd)

def pdfsandwich(in_prefix, out_prefix, **args):
    'adds a searchable text layer to a pdf'
    in_filename  = path(in_prefix,  '.pdf')
    out_filename = path(out_prefix, '.pdf')
    cmd = [ 'pdfsandwich', in_filename
          , '-o', out_filename
          #, '-quiet'
          ]
    if args['verbose']:
        print(' '.join(cmd))
    subprocess.check_call(cmd)

### command line ###

def parse(given):
    'parses command line argments into a dict'
    expected = \
        [ ('-n', '--name'      , {'default':name()         })
        , ('-s', '--source'    , {'default':'ADF'          })
        , ('-m', '--mode'      , {'default':'Lineart'      })
        , ('-d', '--duplex'    , {'action':'store_true'    })
        , ('-v', '--verbose'   , {'action':'store_true'    })
        , ('-o', '--open'      , {'action':'store_true'    })
        , ('-p', '--pages'     , {'type':int, 'default': -1})
        , ('-r', '--resolution', {'type':int, 'default':200})
        , ('-x', '--width'     , {'type':int, 'default':215})
        , ('-y', '--height'    , {'type':int, 'default':275})
        ]
    parser = argparse.ArgumentParser()
    for arg in expected:
        parser.add_argument(*arg[:-1], **arg[-1])
    recognized = parser.parse_args(given)
    return recognized.__dict__

# TODO consistent variable names
# TODO rotate images
# TODO remove blank pages
# TODO separate scan, process, and ocr steps (ocr might fail)
# TODO ask to overwrite existing pdf
# TODO get ocr working on arch
# TODO use temp folders instead of prefixes

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

if __name__ == '__main__':
    args = parse(sys.argv[1:])
    #cmds = [scanimage, convert, tiffcp, tiff2pdf, mv]
    cmds = [scanimage, convert, tiffcp, tiff2pdf, pdfsandwich, mv]
    chain(*cmds, **args)
    xdg_open(**args)
