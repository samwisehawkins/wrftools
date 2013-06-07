class ConversionError(Exception):
    pass
    
class ConfigError(Exception):
    pass
    
class DomainError(Exception):
    """Represents an error trying to access a grid point outside the model domain """
    pass