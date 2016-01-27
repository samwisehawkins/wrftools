import datetime


def get_time(base_time=None, delay=None, round=None):
    """ Returns base_time minus a delay in hours, rounded down to the nearest hour given in round.
    Warning - works by rounding back to the beginning of the day, and does not currently work for the 
    case where you request a cycle time which is later than the base_time
    
    Arguments:
        base_time  -- base time to calculate from
        delay  -- optional delay in hours to apply 
        round  -- a list of integer hours to restrict the return value to e.g. [0,6,12,18]"""
    


    hour  = datetime.timedelta(0, 60*60)

    base_time = base_time if base_time else datetime.datetime.today()
    
    delay = delay if delay else 0
    delayed_time  = base_time - delay * hour

    start = delayed_time
    if round:
        start_day   = datetime.datetime(delayed_time.year, delayed_time.month, delayed_time.day, 0, 0)           # throw away all time parts
        start_hour  = delayed_time.hour
        past_hours  = [ h for h in round if (h <= start_hour)]
        recent_hour = past_hours[-1]
        start       = start_day + recent_hour * hour
    

    return start