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

 # WRF        - natch
 # WPS        - natch
 # gribmaster - fetches external boundary conditions
 # NCL        - for visualisation and time-series extraction
 # NCO        - needed for adding metadata and compression

Despite trying to reduce the python dependencies to a bare minimimum, 
there are still some modules which are not included with a standard
python installation. These are:

 # pyyaml - needed if yaml is used for config files (recommended)
 # docopt - intelligent parsing of command-line arguments

## Quick start

 1. Clone wrftools repository
 2. Create a local working directory 
 3. Link the run_forecast.py into working directory
 4. Copy examples/forecast.yaml into working directory
 5. Edit the new forecast.yaml file
 6. $> python run_forecast.py --config=forecast.yaml


## Usage

Basic usage is:

    $> python run_forecast.py --config=<config_file>

Any configuration options can also be specified on the command-line, where they will override 
those in the config file e.g.

    $> python run_forecast.py --config=<config_file> --log_level=debug

See examples/forecast.yaml for an explanation of options

## Modularity

In the beginning, everything (preparation, simulation, post-processing, visualisation, time-series extraction) 
ran from a single script. This is convenient to schedule from an operational perspective, and once it's done it's done. 
However, it becomes unweildy when you need to re-run certain parts e.g. only the visualisation, or only the post-processing. 

The design has now evolved into a more modular structure, but one that allows all of the modules to be run together if so desired. 
I will call these modules components, to distinguish them from pure python modules.  There are currently the following components:

 # fetch          - a thin wrapper around gribmaster
 # prepare        - ensures correct files present, does some linking, updates namelist files
 # simulate       - runs WPS and WRF
 # post (process) - adds metadata, compresses files
 # visualise      - calls NCL with specified scripts. Note the English (i.e. correct ;) spelling
 # extract        - extracts time-series of variables at specified locations
 # finalise       - removes files, transfer locally, archive etc. 
 # dispatch       - send out emails, plots etc


Each component can be run stand-alone, with a configuration file. Alternatively the
run_forecast.py script will run all components specified.

## Configuration

For explanation of configuration options, see examples/forecast.yaml.

Configuration is done via a config file, alhough options can also be overwridden 
at the command line. json and yaml formats are understood. json has the advantage
that a parser is included in standard python distributions. 
However, I prefer YAML since the syntax is clearer, and the files can be commented.

Within a config file, environment variables can be specified accessed using ${var}.
Local variables defined elsewhere in tht config file can be specified  using %(var).
If the variable in ${} or %() is not defined within the current environments,
it will not be expanded. This is not part of standard yaml or json!

Additional files can be specified using %(file.json) or %(file.yaml). These will
be read and expanded in-place, similar to an inlcude directive. 

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

  web_dir = %(working_dir)/web/%fHZ


Some options in the configution. e.g. start time, maximum number of nests, 
** will override settings in the namelist.input and namelist.wps files **


## Directories

Most things happen in directories relative to the **working directory**, as specified in 
the config option 'working_dir'.  Using the default set of options, the following directories
are created and used:

 # working_dir/wps        - WPS executables get linked and run here
 # working_dir/wrf        - WRF executables get linked and run here
 # working_dir/wrfout     - wrfout files are moved here after completion
 # working_dir/tseries    - time series get extracted here


## Preparation and finalising

In the prepration and finalisation stages, various cleanup and archive operations can be achived by supplying arguments to 
the: 

    # prepare.create   directories will 
    # prepare.remove
    # prepare.link
    # prepare.copy

 
 
 
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
