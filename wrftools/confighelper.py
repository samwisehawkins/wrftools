"""config.py provides general configuration handling.

Dependencies: json or yaml, docopt

config.py allows options to be specified in a json or yaml config file and overridden on the command line. 
The range of valid options can be specified in the docstring as optional options i.e surrounded by
square braces [--option], to make the usage pattern meaninful. 

To use this module within another python module, import and call the config function with the calling modules docstring
and command line arguments:
    
    "modules docstring in docopt recognised format"
    
    import config as conf
    config = conf.config(__doc__, sys.argv[1:] )

Potential gotcha is that any defaults specified in the docstring will override those specified in the config file. 
Therefore it is preferrable not to specify defaults in the docstring, but place them in a defaults config file. 

Another gotcha is that the options will come back stripped of preceding "--", this is to allow the equivalent 
options to be specified in the config file without leading "--". 

As an example, this module can be run from the command line:

Usage: 
    config.py [--config=<file>]
              [--config-fmt=<fmt>]
                [--option1=arg1]
                [--option2=arg2]
                [--option3=arg3]
                [--option4=arg4]
                [--option5=arg5]
Options:
        --config=<file>    configuration file to specify options
        --config-fmt=<fmt> configuration file format [default: JSON]
        --option1=arg1     anything specified here will ovveride the config file 
        --option2=arg2      
        --option3=arg3
        --option4=arg4
        --option5=arg5 """


import sys
import os
import re
import docopt


# Supported file format extentions
JSON = ["json"]
YAML = ["yaml", "yml"]    

EVAR  = re.compile('\$\(.*?\)')                              # match rows containing environment vars
LVAR  = re.compile('%\(.*?\)')                               # match rows containing local vars 
CVAR = [re.compile('%\(.*\.'+e+'\)' ) for e in JSON + YAML]  # match rows containing config file specifiers


class ConfigError(Exception):
    pass


def main():
 
    c = config(__doc__, sys.argv[1:] )
    
    # Need these for pretty printing
    import json       
    def date_handler(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj
    
    print json.dumps(c, indent=4, default=date_handler)
   

def config(docstring, args, format="json"):
    cargs  = docopt.docopt(docstring,args)
    
    if '--config-fmt' in cargs and cargs['--config-fmt']:
        format = cargs['--config-fmt']
    
    if format in JSON:
        import json

    elif format in YAML:
        import yaml
        
    cargs = {key.lstrip("--"): cargs[key] for key in cargs.keys()}
    
    cargs = parse_cmd_args(cargs, format=format)

    if 'config' in cargs and cargs['config']:
        cfile = load(cargs['config'])
        config = merge(cargs, cfile)
        return config
    else:
        return cargs


def load(fname, evar=EVAR, lvar=LVAR, cvar=CVAR, flatten=False, format=None):
    """Loads a config file, and recursively opens any subsets specified 
        by a reference to another config file. Suppose in the parent we have:
        option1: value1
        option2: value2
        option3: %(config2.yaml)
    
    
    where config2.yaml looks like:
    
        option2: value3
        option4: value4
    
    Then config2.yaml will be read and parsed. If flatten is false, the resulting dictionary
    will look like:
    
        option1: value1
        option2: value2
        option3:
            option2: value3
            option4: value4

    Whereas if flatten=true, then config2 will **update** the parent, delete the key which held the file,
    potentially overwriting values:
    
    option1: value1
    option2: value3
    option4: value4 
    
    This second option can be used like an include directive by specifying exlusive keys e.g.
    include1: config1.yaml
    include2: config2.yaml
    include3: config3.yaml"""
    
    
    
    if format==None:
        format = fname.split(".")[-1]    
    if format in JSON:
        import json
    elif format in YAML:
        import yaml
    else:
        raise ConfigError("config format not supported")
    
    confstr = open(fname, 'r').read()
    confstr = expand_evar(confstr, os.environ, evar)
    
    if format in JSON:
        parent=json.loads(confstr)
    
    if format in YAML:
        parent = yaml.load(confstr)
    
    for key,value in parent.items():
        if isinstance(value, (str, unicode)) and any(regex.match(value) for regex in cvar):
            subfname = value[2:-1]
            subconf = load(subfname,evar, lvar, cvar, flatten=flatten, format=format)
            if flatten:
                parent.update(subconf)
                del(parent[key])
            else:
                parent[key] = subconf

    expand_lvar(parent, lvar)
    
    return parent

    
def expand_lvar(dictionary, lvar):
    return _expand_lvar({}, dictionary, lvar)
    
    
def _expand_lvar(parent, current, lvar):
    """ Replaces %(local_var) definitions with their original definition. Only searches 
    in immediate parent scope, need to defined recursing up the tree"""
    
    search_next = []
    for key,value in current.items():
        if isinstance(value, (str, unicode)) and lvar.match(value):
            lvars = lvar.findall(value)
            for lv in lvars:
                lvname = lv[2:-1]
                if lvname in current:
                    value = value.replace(lv, current[lvname])
                elif lvname in parent:
                    value = value.replace(lv, parent[lvname])
            current[key] = value
            
        elif isinstance(value, dict):
            search_next.append(key)
    
    for key in search_next:
        _expand_lvar(current, current[key], lvar)
    

def expand_evar(s, env, expr):
    vars = expr.findall(s)
    for v in vars:
        vname = v[2:-1]
        if vname in env:
            s = s.replace(v, env[vname])
        else: pass
    return s
    
def merge(dict_1, dict_2):
    """Merge two dictionaries.    
    Values that evaluate to true take priority over falsy values.    
    `dict_1` takes priority over `dict_2`.    """    
    
    return dict((str(key), dict_1.get(key) or dict_2.get(key))
            for key in set(dict_2) | set(dict_1))


def parse_cmd_args(args, format="json"):
    """Parse command line arguments which look like lists as json/yaml
    
    Arguments: 
        args -- a dictionary mapping argument names to their values
        
    Returns:
        a new dictionary with any list-like values expanded"""
    
    jargs = {}
    # match list expression or dictionary expression
    exp = re.compile("(\[.*\]) | (\{.*\})")
    lexpr =  re.compile("\[.*\]")
    dexpr =  re.compile("\{.*\}")

    if format in JSON:
        import json
    elif format in YAML:
        import yaml
    else:
        raise ConfigError("configuration format: %s not understood, use json or yaml" % format)
      
    for (k,v) in args.items():
        if v and type(v)==type("") and ( lexpr.match(v) or dexpr.match(v)):
            if format in JSON:
                jv = json.loads(v)
            elif format in YAML:
                jv = yaml.load(v)

            jargs[k] = jv
        else:
            jargs[k] = v
    
    return jargs




    
if __name__ == '__main__':
    main()
        
