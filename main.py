#!/usr/bin/env python

# will get variables: it and outputpath

def setup_simulation():
    pass

def simulate():
    pass

def store_files():
    with open(outputpath + '/output' + str(it) + '.dat', 'w') as fh:
        fh.write('done :-)\n')
        fh.write(str(it - 1))

def run(*arguments, **kwargs):
    setup_simulation()
    simulate()
    store_files()

    print ('I have run with ' + str(arguments) + str(kwargs))
    pass

if __name__ == '__main__':
    it = 1
    outputpath = '.'
    run()
