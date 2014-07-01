"""confighelper.py provides general configuration handling.

Dependencies: json or yaml, docopt

confighelper.py allows options to be specified in a json or yaml config file **and** overridden on the command line. 
To use this module, import and call the config function passing in the calling module's docstring
and command line arguments e.g.
    
    mymodule.py
    "mymodule.py docstring in docopt recognised format"
    
    import confighelper as conf
    config = conf.config(__doc__, sys.argv[1:] )

Potential gotcha is that any defaults specified in the docstring will override those specified in the config file. 
Therefore it is preferrable not to specify defaults in the docstring, but place them in a defaults config file. 

Command-line options are stripped of preceding "--", to allow the equivalent 
options to be specified in the config file without leading "--". 

As an example, this module can be run from the command line:

Usage: 
    confighelper.py [--config=<file>]
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
from collections import OrderedDict
import pprint

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
    
    # Need this for pretty printing
    import json       
    def date_handler(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj
    
    print json.dumps(c, indent=4, default=date_handler)
   

def config(docstring, args, format="json", flatten=False):
    """ this is the primary function, which takes a modules's docstring, 
    a list of command line arguments (as in sys.argv[1:]) and returns a 
    merged dictionary which is the result of reading any file specified
    by a --config argument, and then merging into that any other command-line
    arguments. 
    
    Arguments:
    docstring -- calling module's docstring in docopt recognised format
    args      -- command line arguments as in sys.argv[1:]
    format    -- format for parsing configuration files (default json)
    flatten   -- how to deal with hierachical inclusion of config files """
    
    cargs  = docopt.docopt(docstring,args)
        
    if '--config-fmt' in cargs and cargs['--config-fmt']:
        format = cargs['--config-fmt']
    
    elif '--config' in cargs and cargs['--config']:
        format = cargs['--config'].split('.')[-1]
    
    
    
    if format in JSON:
        import json

    elif format in YAML:
        import yaml

    # strip command line arguments of leading --
    cargs = {key.lstrip("--"): cargs[key] for key in cargs.keys()}
    
    # always parse command-line arguments as yaml, as this saves having to put quotes around arguments
    cargs = parse_cmd_args(cargs, format="yaml")

    # if a config file is specified, and is not 'falsy'
    if 'config' in cargs and cargs['config']:
        cfile = load(cargs['config'], flatten=flatten)
        merged = merge(cargs, cfile)
        return merged
    else:
        return cargs


       
        
def load(fname, evar=EVAR, lvar=LVAR, cvar=CVAR, flatten=False, format=None):
    """Loads a config file, and recursively opens any included config files 
    
    Arguments:
    fname -- name of the file to load
    evar  -- regular expression matching environment variable definition
    lvar  -- regular expression matching local variable definition
    cvar  -- regular expression matching included config file  definition
    flatten -- how to merge hierachical nested config files, see below
    format -- format to use for config file, json or yaml, default determine by file extension
    
    Suppose in the parent we have:
        
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
    
    path, name = os.path.split(fname)
    
    confstr = open(fname, 'r').read()
    confstr = expand_evar(confstr, os.environ, evar)
    
    if format in JSON:
        parent=json.loads(confstr)
    
    if format in YAML:
        parent = yaml.load(confstr)

        
    for key,value in parent.items():
        if isinstance(value, (str, unicode)) and any(regex.match(value) for regex in cvar):
            subfname = value[2:-1]
            subconf = load(path+"/"+subfname,evar, lvar, cvar, flatten=flatten, format=format)
            if flatten:
                parent.update(subconf)
                del(parent[key])
            else:
                parent[key] = subconf


    tree = parent.copy()
    scope = parent.copy()
    result = expand_tree(tree, scope, lvar)
    
    return result
        
        
def stringy(value):
    return isinstance(value, (str, unicode))

def listy(value):
    return hasattr(value, "__getitem__") and not stringy(value)    


def expand(string, scope, expr):
    """ Replaces an expression in string by looking it up in scope"""
    result = string

    # if no local variable definitions in string
    if not expr.search(result):
        return result
    
    # loop through each local variable 
    exprs = expr.findall(string)
    for ex in exprs:
        expanded = lookup(ex, scope)
        
        # if it hasn't changed,then we can stop 
        if not expanded:
            continue
        
        # otherwise we test whether there are still expressions in the string
        elif expr.search(expanded):
            expanded = expand(expanded, scope, expr)
        result   = result.replace(ex, expanded)
    return result

def lookup(string, scope):
    """ lookup a string within a dictionary and return result. If string not found, 
    returns None """
    
    name = string[2:-1]
    if name in scope:
        result = scope[name]
        if not stringy(result):
            raise Exception("expressions must refer to strings defined elsewhere: %s resolves to type %s" %(string, type(result)))
        return result


def isnode(node):
    return type(node)==type({})
        
        
def isleaf(node):
    return not isnode(node)
    
def expand_tree(tree, scope, expr):
    for key, node in tree.items():
        if isleaf(node):
            new_node = expand_leaf(node, scope, expr)
       
        elif isnode:
            new_node = expand_tree(node, scope, expr)
        
        tree[key] = new_node
    return tree    

    
def expand_leaf(node, scope, expr):
    if stringy(node):
        return expand(node, scope, expr)
    elif listy(node):
        f = lambda n: expand_leaf(n, scope, expr)
        return map(f, node)
    else:
        return node


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
    
    # values that are None do not override
    return dict((str(key), choose(key, dict_1, dict_2)) for key in set(dict_2) | set(dict_1))
    
    return dict((str(key), dict_1.get(key) or dict_2.get(key))
            for key in set(dict_2) | set(dict_1))

            
def choose(key, dict1, dict2):
    v1 = dict1.get(key)
    v2 = dict2.get(key)
    if v1!=None:
        return v1
    else:
        return v2

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
        #if v and type(v)==type("") and ( lexpr.match(v) or dexpr.match(v)):
        if v and type(v)==type(""):

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
        
