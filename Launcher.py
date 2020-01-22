#!/usr/bin/env python

import glob, os, shutil, stat, subprocess, sys
import numpy as np
from os.path import expanduser
HOME = expanduser("~")
CWD  = os.getcwd()

import socket
hostname = socket.gethostname()

WRKDIRBASE = (os.path.abspath('..') + '/Simulations/')

if 'lxkb' in hostname:
    print ('\n*** LAUNCHING FOR KRONOS ***\n')
    raise NotImplementedError('to be set up')
else:
    sessionname = 'runsims'
    print ('\n*** LAUNCHING LOCALLY VIA TMUX SESSION "{}" ***\n'.format(sessionname))

# ==== Simulation Working Directory
WRKDIR = WRKDIRBASE + '2020-01-22--coolstuff/'

# ==== Directory that contains the base cfg file with name filename
SRCDIR = CWD
SUFFIX = 'testing'

# ==== Simulation parameters
Qx = np.linspace(18.55, 18.95, 5)
Qy = np.linspace(18.55, 18.95, 5)

def launch(Qx, Qy, hostname):

    wrkdir = create_directories(WRKDIR, SRCDIR)

    # Prepare scan

    for i, v in enumerate(Qx):
        for j, w in enumerate(Qy):
                    write_scan_files(
                        wrkdir,
                        i*len(Qx) + j,
                        ('Qx={0:g}, Qy={1:g}').format(
                                v, w)
                    )

    if 'lxbk' in hostname:
        submit_to_kronos(wrkdir,)
    else:
        # run locally in tmux windows
        subprocess.call(['tmux', 'new', '-d', '-s', sessionname, 'ipython'])
        # trigger first simulation run:
        subprocess.call(['tmux', 'send', '-t', sessionname,
                         '!touch {}/Output/finished0'.format(wrkdir), 'Enter'])

        for v in Qx:
            for w in Qy:
                subprocess.call(['tmux', 'new-window', '-t', sessionname])
                tmux_window_id = subprocess.check_output(
                    ['tmux', 'display-message', '-p', '#I']).decode('utf8').rstrip()
                # log everything:
                subprocess.call(['tmux', 'pipe-pane', '-t', sessionname,
                                 'cat>{}/Output/tmux.{}.log'.format(
                                    wrkdir, tmux_window_id)])
                subprocess.call(['tmux', 'send', '-t', sessionname,
                                 '# running at Qx {:g} and Qy {:g}'.format(v, w),
                                 'Enter'])
                subprocess.call(['tmux', 'send', '-t', sessionname,
                                 'cd {}'.format(wrkdir), 'Enter'])

                subprocess.call(['tmux', 'send', '-t', sessionname,
                                 # wait until the previous run has finished:
                                 'while [ ! -e Output/finished{0} ]; do sleep 1; done; '
                                 # run the simulation:
                                 'python task.{1}.py && '
                                 # trigger next run after finishing this one:
                                 'touch Output/finished{1}'.format(
                                    int(tmux_window_id) - 1, tmux_window_id),
                                 'Enter'])



def create_directories(wrkdir, srcdir, casdir=None, locdir=None):

    # Catch potential slash at end of path
    if srcdir.split('/')[-1] == '':
        extension = srcdir.split('/')[-2]
    else:
        extension = srcdir.split('/')[-1]

    # Make directories
    newrkdir = wrkdir + '/' + extension + '_' + SUFFIX
    if os.path.exists(newrkdir):
        while True:
            ans = raw_input('\nWARNING: Path ' + newrkdir +
                            ' already exists! Overwrite? [yes or no]\n')
            if ans in ('y', 'ye', 'yes'):
                shutil.rmtree(newrkdir)
                break
            if ans in ('n', 'no'):
                print ('\nAborting...')
                exit(0)
            print ('\nPlease answer "yes" or "no"!')

    shutil.copytree(srcdir, newrkdir)
    os.mkdir(newrkdir + '/Data')
    os.mkdir(newrkdir + '/Output')

    return newrkdir


def write_scan_files(wrkdir, it, kwargstr):

    with open(wrkdir + '/task.' + str(it + 1) + '.py', 'wt') as file:
        file.write('import main\n\n')
        file.write('main.it=' + str(it + 1) + '\n')
        file.write('main.outputpath="' + wrkdir + '/Data"\n')

        file.write('print ("****** Running at ' + kwargstr + '!")\n\n')
        file.write('main.run(' + kwargstr + ')\n\n')


def submit_to_kronos():
    pass
    # similar to bsub_to_hpcbatch below for example..
"""
def bsub_to_hpcbatch(wrkdir, jobmin=1, jobmax=1, libraries=None,
                     prefix='', casdir=None, locdir=None):

    os.chdir(wrkdir)

    with open('myjob.lsf', 'w') as file:
        file.write('#!/bin/bash')
#        file.write('\nmodule load compilers/cuda-8.0')
        file.write('\nmodule load compilers/cuda-7.5')
        file.write('\nnvcc --version')
        file.write('\nnvidia-smi')
        file.write('\nexport PATH="/home/HPC/oeftiger/anaconda/bin:$PATH"')
        file.write('\nwhich python')
        file.write('\n\ncd ' + wrkdir)
        file.write('\n\nulimit -c 0')
        file.write('\n\npython tmppyheadtail.$LSB_JOBINDEX')
        file.write('\nls -l')

        file.write('\n\necho -e "\\n\\n******** LSF job successfully completed!"')
        # file.write('\n\necho -e "\\n******** Now copying output files..."')
        # file.write('\ncp *.h5 ' + wrkdir + '/Data')

        file.write('\necho -e "HOSTNAME: "')
        file.write('\nhostname')
        file.write('\necho -e "\\n"')
        file.write('\ncat /proc/cpuinfo')
        file.write('\necho -e "\\n*** DEBUG END ****"')

    print ('\n*** Submitting jobs ' + prefix + ' to LSF...')

    for i in range(int(jobmax / JCHUNK) + 1):
        a = i * JCHUNK + 1
        b = (i + 1) * JCHUNK
        if b > jobmax: b = jobmax

        lsfcommand = ['bsub', '-L /bin/bash', '-N ',
                      '-e ' + wrkdir + '/Output/stderror.%J.%I.log ',
                      '-o ' + wrkdir + '/Output/stdout.%J.%I.log',
                      '-J ' + prefix + '[' + str(a) + '-' + str(b) + ']',
                      '-u ' + EMAIL, '-q ' + QUEUE, '< myjob.lsf']
        if EXTRA_ARGS:
            lsfcommand.insert(1, EXTRA_ARGS)
        if PARALLEL:
            lsfcommand.insert(1, '-n 8 -R "span[hosts=1]"')
        lsfcommand = ' '.join(lsfcommand)
        print ('Executing submission with command: ' + lsfcommand)

        with open('launch' + str(i + 1), 'wt') as file:
            file.write("#!/bin/bash\n")
            for lsfc in lsfcommand:
                file.write(lsfc)
        os.chmod("launch" + str(i + 1), 0777)
        subprocess.call("./launch" + str(i + 1))
"""

if __name__ == "__main__":
    launch(Qx, Qy, hostname)
