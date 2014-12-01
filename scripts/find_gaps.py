"""find_gaps.py finds missing files in a sequence based on date

Usage: find_gaps.py --start=<YYYY-mm-dd_HHMM> --end=<YYYY-mm-dd_HHMM> --freq=<hours> --fmt=<str> [--verbose]  <file_pattern>

    Options:
        --start=<output>    start date of file sequence
        --end=<m>           end date of file sequence
        --freq=<g>          number of hours between file times
        --fmt=<str>         date format to parse start and end argumments [default: %Y-%m-%d_%H]
        --verbose           print more information
        <file_pattern> pattern which would render filename when date substited in


"""

import docopt
import os
import sys
import time,datetime
from dateutil import rrule

def main(args):
    ttuple = time.strptime(args['--start'], args['--fmt'])[0:6]
    start = datetime.datetime(*ttuple)
    ttuple = time.strptime(args['--end'], args['--fmt'])[0:6]
    end   = datetime.datetime(*ttuple)
    freq  = int(args['--freq'])
    #path  = args['<path>'] 
    #files = args['<files>']
    rule = rrule.rrule(dtstart=start, until=end, freq=rrule.HOURLY, interval=freq)

    pattern = args['<file_pattern>'].replace('~', os.environ['HOME'])
    expected = [d.strftime(pattern) for d in rule]

    
    #print ' %d files checked'   % len(actual)

    nmissing = 0

    for f in expected:
        if not os.path.exists(f):
            print f
            nmissing+=1

    if args['--verbose']:
        print '********************************'
        print ' sequence start: %s' % start
        print ' sequence end: %s'   % end
        print ' file pattern: %s'   % pattern
        print ' %d files expected'  % len(expected)
        print ' %d files missing'   % nmissing
        print '********************************'

if __name__ == '__main__':
    args = docopt.docopt(__doc__, sys.argv[1:])
    main(args)

