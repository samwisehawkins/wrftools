"""find_gaps.py finds missing files in a sequence based on date

Usage: find_gaps.py --chars=<start,end> [--fmt=<fmt>] [--start=<YYYY-mm-dd_HHMM>] [--end=<YYYY-mm-dd_HHMM>]  [--freq=<str>] [--verbose]  <files>...

    Options:
        --chars=<start,end> start and end index of date within filenames
        --start=<start>     start date of file sequence, if None, first file is use
        --end=<end>         end date of file sequence, if None, last file is used
        --freq=<hours>      number of hours between file times, if None, difference between first two files is used
        --fmt=<fmt>         date format to parse start and end argumments [default: "%Y-%m-%d %H"]
        --verbose           print more information
        <files>             files to check for gaps


"""

import docopt
import os
import sys
import time,datetime
from dateutil import rrule

def parsedate(token, fmt):
    ttuple = time.strptime(token, fmt)[0:6]
    return datetime.datetime(*ttuple)

        
def main(args):
    files = map(os.path.basename, args['<files>'])
    chars = map(int, args['--chars'].split(','))
    assert len(chars)==2
    
    # start index, end index
    si = chars[0]
    ei = chars[1]
    
    # supply format argument to parser function
    fmt = args['--fmt']
    parse = lambda s: parsedate(s, fmt)

    dateparts = [f[si:ei] for f in files]
    filedates = [parse(d) for d in dateparts]
   
   
    if args.get('--start'):
        start=parse(args['--start'])
    else:
        start = filedates[0]

    if args.get('--end'):
        end=parse(args['--end'])
    else:
        end = filedates[-1]


    if args.get('--freq'):
        freq  = int(args['--freq'])
    else:
        delta = filedates[1] - filedates[0]
        freq = delta.days*24+delta.seconds/(60*60)
    

    rule = rrule.rrule(dtstart=start, until=end, freq=rrule.HOURLY, interval=freq)
    alldates = list(rule)

    missing = [d for d in alldates if d not in filedates]


    for d in missing:
        print d.strftime(fmt)
    


    if args['--verbose']:
        print '********************************'
        print ' sequence start: %s' % start
        print ' sequence end: %s'   % end
        print ' %d files expected'  % len(alldates)
        print ' %d files missing'   % len(missing)
        print '********************************'

if __name__ == '__main__':
    args = docopt.docopt(__doc__, sys.argv[1:])
    main(args)

