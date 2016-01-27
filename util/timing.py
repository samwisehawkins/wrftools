"""timing.py computes timing information from a rsl output file from WRF

Usage: 
    python timing.py rsl_file [namelist.input]"""


import sys, os
# this is an ugly hack to do a relative import, but it works
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wrftools'))
import namelist as nl
import re

def main():
    """Reads a rsl file from WRF and works out timing information
    from that """

    args = sys.argv[1:]
    
    print('*** Computing timing information ***')
    rsl_file = args[0]
    
    if len(args)>1:
        namelist = nl.read_namelist(args[1])
        timestep = namelist.settings['time_step'][0]
    else:
        timestep=None
    
    f              = open(rsl_file, 'r')
    lines          = f.read().split('\n')
    
    # get timings on outer domain
    main_times  = [float(l.split()[8]) for l in lines if re.search("^Timing for main: time .* 1:", l)]
    total       = sum(main_times)
    steps       = len(main_times)
    time_per_step = (total/steps)
    x_real       = timestep / time_per_step if timestep else None
    
    m, s = divmod(total, 60)
    h, m = divmod(m, 60)
    
    
    
    print('\n*** TIMING INFORMATION ***')
    print('\t %d outer timesteps' % steps)
    print('\t %0.3f elapsed seconds' % total)
    print('\t %d:%02d:%02d' % (h, m, s))
    print('\t %0.3f elapsed seconds' % total)
    print('\t %0.3f seconds per timestep' % time_per_step )
    if timestep:
        print('\t %0.3f times real time' %x_real)
    print('*** END TIMING INFORMATION ***\n')    
    
    
if __name__ == '__main__':
    main()