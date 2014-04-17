README
--------

A set of python scripts for running WRF and associated
programmes, e.g. WPS, NCL etc.

It is designed to be quickly hackable. There are some tools out there
which run WRF, but they are not easily modified. This is designed to provide 
an easy to use framework which is easily customised and modified. 

This README file serves as documentation in the (hopefully temporary)
absence of dedicated documentation. 

## Dependencies

The following external tools are required:

* WRF        - obviously
* WPS        - ditto
* gribmaster - fetches external boundary conditions
* NCL        - for visualisation and time-series extraction
* NCO        - needed for adding metadata and compression (compiled with netCDF4 support)

Despite trying to reduce the python dependencies to a bare minimimum, 
there are still some modules which are not included with a standard
python installation. These are:

* pyyaml - needed if yaml is used for config files (recommended)
* docopt - intelligent parsing of command-line arguments

## Quick start

 1. Clone wrftools repository
 2. Create a local working directory 
 3. Link the run_forecast.py into working directory
 4. Copy `examples/forecast.yaml` into working directory
 5. Edit the new forecast.yaml file
 6. `$> python run_forecast.py --config=forecast.yaml`


## Usage

Basic usage is:

    $> python run_forecast.py --config=<config_file>

Any configuration options can also be specified on the command-line, where they will override 
those in the config file e.g.

    $> python run_forecast.py --config=<config_file> --log_level=debug

See examples/forecast.yaml for an explanation of options

## Modularity

The design is slowly evolving into a more modular structure, but one that allows all of the modules to be run together if so desired. 
I will call these modules components, to distinguish them from pure python modules.  There are currently the following components:

* fetch          - a thin wrapper around gribmaster
* prepare        - ensures correct files present, does some linking, updates namelist files
* simulate       - runs WPS and WRF
* post (process) - adds metadata, compresses files
* visualise      - calls NCL with specified scripts. Note the English (i.e. correct ;) spelling
* extract        - extracts time-series of variables at specified locations
* finalise       - removes files, transfer locally, archive etc. 
* dispatch       - send out emails, plots etc


Each component can be run stand-alone, with a configuration file. Alternatively the
run_forecast.py script will run all components specified.

## Configuration

For explanation of configuration options, see examples/forecast.yaml.

Some options in the configution. e.g. start time, maximum number of nests, 
** will override settings in the namelist.input and namelist.wps files **

Configuration is done via a config file, alhough options can also be overridden 
at the command line. json and yaml formats are understood. json has the advantage
that a parser is included in standard python distributions. 
However, I prefer YAML since the syntax is clearer, and the files can be commented.

Within a config file, environment variables can be specified accessed using `${var}`.
Local variables defined elsewhere in tht config file can be specified  using `%(var)`.
If the variable in `${}` or `%()` is not defined within the current environments,
it will not be expanded. This is not part of standard yaml or json!

Additional files can be included using %(file.json) or %(file.yaml). The default 
behaviour is to read and merge these directly into the parent scope,  in a manner
similar to an inlcude directive. That is, suppose we have: 

    config1.yaml
    option1: value1
    option2: value2
    option3: %(config2.yaml)
    
    
and config2.yaml looks like:
    config2.yaml
    option2: value3
    option4: value4
    
Then when config1.yaml is read and expanded, config2 will **update** the parent, 
potentially overwriting values:
    
    option1: value1
    option2: value3
    option4: value4 
    
For that reason, it is recommended that where required, keys are kept unique
using a hierachical naming convention using '.' as seperators.

Times can be specified using the following syntax, %cX, where c can be:
  
    i -- initial time 
    v -- valid time 
    f -- forecast lead time

And X follows the a subset of python conventions for date and time formatting:

    %y -- 2-digit year
    %Y -- 4-digit year
    %m -- 2 digit month
    %d -- 2-digit day
    %H -- 2 digit hour
    %M -- 2-digit minute
    %S -- 2-digit second 


Example:

    web_dir = %(working_dir)/web/%iHZ

will be expanded to:

    web_dir = /path/to/work/dir/web/00Z
    web_dir = /path/to/work/dir/web/12Z

depending on the initial time of the forecast.

Some options in the configution. e.g. start time, maximum number of nests, 
** will override settings in the namelist.input and namelist.wps files **


## Directories

Most things happen in directories relative to the **working directory**, as specified in 
the config option 'working_dir'.  Using the default set of options, the following directories
are created and used:

* working_dir/wps        - WPS executables get linked and run here
* working_dir/wrf        - WRF executables get linked and run here
* working_dir/wrfout     - wrfout files are moved here after completion
* working_dir/tseries    - time series get extracted here
* working_dir/plots      - plots placed here


## Preparation and finalising

In the prepration and finalisation stages, various cleanup and archive operations can be achived by supplying arguments to 
the: 

* prepare.create   list of directories to create during the prepare phase
* prepare.remove   list of arguments to be passed to consecutive `rm` commands during prepare phase
* prepare.link     list of arguments to be passed to consecutive `ln` commands during prepare phase
* prepare.copy     list of arguments to be passed to consecutive `cp` commands during prepare phase
* prepare.move     list of arguments to be passed to consecutive `mv` commands during prepare phase

Similarly, the same options can be specified for the finalise.* options. These will be executed after simulation
post processing and visualisation.  In this way, file archiving and cleanup can be specified in a very general way.
Some of the commands rely on underlying linux system call, and therefore may not work on macs. In future they should
be replaced by python equivalents to ensure better compatibility.
 
 
----------
Author 
Sam Hawkins
samwisehawkins@gmail.com

---------
License
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>i
