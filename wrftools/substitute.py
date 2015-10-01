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

    
def date_replacements(init_time=None, valid_time=None, end_time=None):    
    """ Generate dictionay of replacements"""
    
    result = {}
    
    if init_time:
    
        yi  = str(init_time.year)[2:]
        Yi  = str(init_time.year)
        mi  = '%02d' % init_time.month
        di  = '%02d' % init_time.day
        Hi  = '%02d' % init_time.hour
        Mi  = '%02d' % init_time.minute
        Si  = '%02d' % init_time.second

        
        result['%iY'] = Yi
        result['%iy'] = yi
        result['%im'] = mi
        result['%id'] = di
        result['%iH'] = Hi
        result['%iM'] = Mi
        result['%iS'] = Si

    if valid_time:
        yv  = str(valid_time.year)[2:]
        Yv  = str(valid_time.year)
        mv  = '%02d' % valid_time.month
        dv  = '%02d' % valid_time.day
        Hv  = '%02d' % valid_time.hour
        Mv  = '%02d' % valid_time.minute
        Sv  = '%02d' % valid_time.second
        
        result['%vY'] = Yv
        result['%vy'] = yv
        result['%vm'] = mv
        result['%vd'] = dv
        result['%vH'] = Hv
        result['%vM'] = Mv
        result['%vS'] = Sv

    if end_time:
    
        ye  = str(end_time.year)[2:]
        Ye  = str(end_time.year)
        me  = '%02d' % end_time.month
        de  = '%02d' % end_time.day
        He  = '%02d' % end_time.hour
        Me  = '%02d' % end_time.minute
        Se  = '%02d' % end_time.second

        
        result['%eY'] = Yi
        result['%ey'] = yi
        result['%em'] = mi
        result['%ed'] = di
        result['%eH'] = Hi
        result['%eM'] = Mi
        result['%eS'] = Si
        
        
        
    if init_time and valid_time:
        delta = valid_time - init_time
        fhr   = delta.days * 24 + int(delta.seconds / (60*60))
        fH    = '%02d' % fhr
        result['%fH'] = fH
    
    return result




    
def sub_date(s, init_time=None, valid_time=None, end_time=None):
    """Substitues a date into a string following standard format codes.
    Syntax of original string s:
    i  -- initial time
    v  -- valid time
    e  -- end time (final valid time)
    %y -- 2-digit year
    %Y -- 4-digit year
    %m -- 2 digit month
    %d -- 2-digit day
    %H -- 2 digit hour
    %M -- 2-digit minute
    %S -- 2-digit second 
    
    Returns: string with codes expanded"""
    replacements =  date_replacements(init_time=init_time, valid_time=valid_time, end_time=end_time)

    for old,new in replacements.items():
        s = s.replace(old, new)
    
    return s