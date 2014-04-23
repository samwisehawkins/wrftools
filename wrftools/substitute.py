import time
import datetime

def expand(s, scope):
    init_time = scope.get('init_time')
    valid_time = scope.get('valid_time')
    grid_id = scope.get('grid_id')
    s = sub_date(s, init_time=init_time, valid_time=valid_time)
    s = sub_grid(s, grid_id)
    return s


def sub_grid(s, grid_id):
    if grid_id:
        s = s.replace('%dd', '%02d' % grid_id)
    return s

def sub_date(s, init_time=None, valid_time=None):
    """Substitues a date into a string following standard format codes.
    Syntax of original string s:
    i  -- initial time
    v  -- valid time
    %y -- 2-digit year
    %Y -- 4-digit year
    %m -- 2 digit month
    %d -- 2-digit day
    %H -- 2 digit hour
    %M -- 2-digit minute
    %S -- 2-digit second 
    
    Returns: string with codes expanded"""
    
    if init_time:
    
        yi  = str(init_time.year)[2:]
        Yi  = str(init_time.year)
        mi  = '%02d' % init_time.month
        di  = '%02d' % init_time.day
        Hi  = '%02d' % init_time.hour
        Mi  = '%02d' % init_time.minute
        Si  = '%02d' % init_time.second

        s = s.replace('%iY', Yi)
        s = s.replace('%iy', yi)
        s = s.replace('%im', mi)
        s = s.replace('%id', di) 
        s = s.replace('%iH', Hi)
        s = s.replace('%iM', Mi)
        s = s.replace('%iS', Si)

    if valid_time:
        yv  = str(init_time.year)[2:]
        Yv  = str(init_time.year)
        mv  = '%02d' % valid_time.month
        dv  = '%02d' % valid_time.day
        Hv  = '%02d' % valid_time.hour
        Mv  = '%02d' % valid_time.minute
        Sv  = '%02d' % valid_time.second
        
        s = s.replace('%vY', Yv)
        s = s.replace('%vy',yv)
        s = s.replace('%vm',mv)
        s = s.replace('%vd', dv) 
        s = s.replace('%vH', Hv)
        s = s.replace('%vM', Mv)
        s = s.replace('%vS', Sv)

    if init_time and valid_time:
        delta = valid_time - init_time
        fhr   = delta.days * 24 + int(delta.seconds / (60*60))
        fH    = '%02d' % fhr
        s = s.replace('%fH', fH)
    
    return s