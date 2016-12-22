wrftools
--------

A framework for preparing WRF simulations.

It is designed to be flexible and extendable. There are some tools out there
which run WRF, but they are not easily modified. This is designed to provide 
a framework which is easily customised and modified. 

## Overview

There are ~~three~~ two main scripts, [init.py](init.py) and [prepare.py](prepare.py) and ~~[submit.py](submit.py). ~~. 

Each block of simulations are run from a `base_dir`. This is the directory which will contain the top-level
namelist files, and the master job scripts. Individual simulations are held in subdirectories named according to 
simulation initial time. e.g. 


    base_dir/namelist.wps              # master namelist templates
    base_dir/namelist.input
    base_dir/scripts                   # master script templates
    base_dir/2015-01-01_00             # simulation directory
    base_dir/2015-01-02_00             # simulation directory



## Install

Since this is not a pure python package, more of a collection of tools

Dependencies:
  * confighelper
  * loghelper
  * pyyaml

## Configuration files
    
The configuration files are yaml, with an extended syntax to allow environment variables,
local variables and date placeholders to be used in the files. See [Configuration](##configuration) for more details.
A subset of configuration file options can be overriden at the command-line, use the `--help` flag with each script to 
see the available command-line options.

## Running scripts

Each script is run in the following way:

     python script.py --config=config.yaml [--log-level=<level>] [--dry-run]  [<times>]

Where config.yaml is a configuration file, `log-level` is one of debug, info or warn, and `dry-run` is a 
boolean flag, and times is either a single time to operate on, or a file specifying a list of times, one per line. 
The reason for using a file, rather than a simple list is that it is more robust to spaces in the times, and requires 
less care about quoting, which always plagues my bash workflow.
    
## Step 1: Initialise

[init.py](init.py) is run once per block of simulations. It creates the master job scripts, copies
configuration files and links the main python scripts into the `base_dir`.

First create the `base_dir` and copy in a `namelist.wps` and `namelist.input`.

    ```
    mkdir mysimulations
    cp namelist.input namelist.wps mysimulations
    cp /path/to/wrftools/config/init.yaml mysimulations
    ```
    
If needed, edit the `init.yaml` file. See [init.yaml](config/init.yaml) for annotated example. The main purpose of  `init.py` 
is to create a subdirectory of *master scripts* which will be used to run each simulation within a block.  Check the 'jobs' entry of `init.yaml` 
to see how these job scripts are created.

    
    ```
    cd mysimulations
    python /path/to/wrftools/init.py --config=init.yaml
    ```

Generation of master scripts is configured by the jobs entry within `init.yaml`. Each sub-entry specifies a 
job template file, a set of replacements to apply, and a target file to write to.  By default these 'master scripts'
are generated within `base_dir/scripts`. 
    
These master scripts can then be edited by hand to provide more control and customisation for whatever post-processing and renaming etc you require. 
These master scripts will get copied and used within each simulation directory, within the same subdirectories e.g.

```
    base_dir/scripts/wrf/wrf.sh       ----->        simulation_dir/wrf/wrf.sh
```    
    
## Step 2: Prepare

[prepare.py](prepare.py) creates the simulation directories, updates `namelist.wps` and 
`namelist.input` files, and copies all of the job submission scripts from the master script directory
into the simulation directories. 

1. Edit `prepare.yaml` to set various directory locations, start time, end time etc. See [config/prepare.yaml](config/prepare.yaml) 
for an example. 

    ```
    python prepare.py --config=prepare.yaml
    ```
     
    
2. `Run prepare.py`
 
Try first without `--link-boundaries` option; it is less likely to fail.
 
    ```
    $> cd ~/mysimulations
    $> python ~/code/wrftools/prepare.py --config=prepare.yaml
    ```

This creates the simulation directories: one for each initial time.  The WRF executables are linked into subdirectories, and the master job scripts
are copied into the appropriate subdirectories.
    
Then try with the  `--link-boundaries` flag. 
    
    ```
    $> python prepare.py --config=prepare.yaml --link-boundaries
    ```    

This checks whether the boundary conditions exist and links     
    
    
## Notes on configuration

Command-line arguments override config file arguments. 

For explanation of configuration options, see [config/prepare.yaml](config/prepare.yaml).

Some options in the configution. e.g. start time, maximum number of nests, 
** will override settings in the namelist.input and namelist.wps files **

Configuration is done via a config file, alhough some options can also be overridden 
at the command line. json and yaml formats are understood. 

Within a config file, environment variables can be specified accessed using `$(var)`.
Local variables defined elsewhere in tht config file can be specified  using `%(var)`.
If the variable in `${}` or `%()` is not defined within the current environments,
it will not be expanded. This is not part of standard yaml or json!

Times can be specified using the following syntax, %cX, where c can be:
  
    i -- initial time 
    v -- valid time 
    f -- forecast lead time (i.e. difference between valid and initial time)

And X follows a subset of python conventions for date and time formatting:

    %y -- 2-digit year
    %Y -- 4-digit year
    %m -- 2 digit month
    %d -- 2-digit day
    %H -- 2 digit hour
    %M -- 2-digit minute
    %S -- 2-digit second 


Example:

    base_dir    = $(HOME)/myforecast
    working_dir = "%(base_dir)/%iY-%im-%id_%iH"
    
becomes e.g. :
    base_dir = /home/dave/myforecast
    working_dir = /home/dave/myforecast/2010-01-01_00



 
----------
Author 
Sam Hawkins
samwisehawkins@gmail.com
---------
