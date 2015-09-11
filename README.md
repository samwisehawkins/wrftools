README
--------

A framework for running WRF simulations.

It is designed to be quickly hackable. There are some tools out there
which run WRF, but they are not easily modified. This is designed to provide 
a framework which is easily customised and modified. 

## Overview

There are two main scripts [prepare.py](prepare.py) and [submit.py](submit.py). 
[prepare.py](prepare.py) creates the directory structure, updates `namelist.wps` and 
`namelist.input` files, and puts all of the job-submission scripts into the right place.
`submit.py` then submits a series of jobs to the scheduler.

A simulation is performed by running:
```
python prepare.py --config=<configuration_file> <optional_command_line_args>
python submit.py --config=<configuration_file> <optional_command_line_args>
```

## Quick start example

Suppose we want to run a simulation configuration called `myforecast`. Assume WRF is in `$HOME/WRF`, and WPS is in `$HOME/WPS`.

1. Clone wrftools repository and **switch to the development branch** :
    
    ```
     $>cd ~/code
     $>git clone https://github.com/samwisehawkins/wrftools.git
     $>cd wrftools
     $>git checkout development
    
    ```
    
2. Create a local base directory to hold all simulations

    ```
    $>mkdir ~/myforecast
    ```

3. Copy namelist files so you have a `~/myforecast/namelist.wps` and `~/myforecast/namelist.input` files as templates
 
 
4. Copy the configuration file `~/code/wrftools/config/prepare.yaml` into the base directory
 
    ```
     $>cp ~/code/wrftools/config/prepare.yaml ~/myforecast
    ```
     
5. Edit the new `~/myforecast/forecast.yaml` file. In particular set:
 
    ```
    base_dir          : $(HOME)/forecasting/myforecast              # the base of the directory tree
    working_dir       : "%(base_dir)/%iY-%im-%id_%iH"               # simulation subdirectories will get named according to initial time
    namelist_wps      : "%(base_dir)/namelist.wps"                  # location of namelist.wps template to use
    namelist_input    : "%(base_dir)/namelist.input"                # location of namelist.input template to use
    wps_dir           : /prog/WPS/3.5                               # location of WPS code
    wrf_dir           : /prog/WRF/3.5        
    ```
    
Note that some of the settings defined here are not used directly, but are defined for convenience fow when they are used later.  
I should improve the docs to mark which ones are essential.
    
    
8. Prepare the directories:
 
 Try this without the `--link-boundaries` option first. It is less likely to fail then.
 
    ```
    $> cd ~/myforecast
    $> python ~/code/wrftools/prepare.py --config=prepare.yaml --start="%Y-%m-%d %H:%M:%S" --end="%Y-%m-%d %H:%M:%S" --init_interval=<hours>
    ```

Then try with the  `--link-boundaries` flag. 
    ```
    $> cd ~/myforecast
    $> python ~/code/wrftools/prepare.py --config=prepare.yaml --link-boundaries --start="%Y-%m-%d %H:%M:%S" --end="%Y-%m-%d %H:%M:%S" --init_interval=<hours>
    ```    

## Configuration

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
