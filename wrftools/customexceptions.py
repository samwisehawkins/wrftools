class ConversionError(Exception):
    pass
    
class ConfigError(Exception):
    pass
    
class DomainError(Exception):
    """Represents an error trying to access a grid point outside the model domain """
    pass
    
class QueueError(Exception):
    """Represents an queueing system error state for a job """
    pass
   
class NamelistError(Exception):
    """Represents an error in the namelist settings file """ 
    pass
    
class MissingFile(Exception):
    """Represents a missing file"""
    pass
    
class InterpolationError(Exception):
    """Interpolation outside data domain"""
    pass