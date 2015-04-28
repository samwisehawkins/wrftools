README
--------

A framework for running WRF and associated programmes, e.g. WPS, NCL etc.

It is designed to be quickly hackable. There are some tools out there
which run WRF, but they are not easily modified. This is designed to provide 
a framework which is easily customised and modified. 

## Quick start

Suppose we want to run a forecast configuration called `myforecast`, and we want the `wrftools` code in
`$HOME/code/wrftools`. In this example, assume WRF is in `$HOME/WRF`, and WPS is in `$HOME/WPS`, and gribmaster is in `$(HOME)/gribmaster`

1. Clone wrftools repository 
    
    ```
     $>cd ~/code
     $>git clone https://github.com/samwisehawkins/wrftools.git
    ```
    
2. Create a local working directory

    ```
    $>mkdir ~/myforecast
    ```

3. Create `~/myforecast/namelist.wps` and `~/myforecast/namelist.input` files
 
 
4. Optionally create a `locations.csv` file for time-series extraction

    ```
    $> cp ~/code/wrftools/example/locations.csv ~/myforecast
    ```
 
5. Link `run_forecast.py` into working directory 
 
    ```
     $>ln ~/code/wrftools/run_forecast.py ~/myforecast
    ```
     
6. Copy `example/forecast.yaml` into working directory 
    
    ```
    $>cp ~/code/wrftools/example/forecast.yaml ~/myforecast 
    ````
 
7. Edit the new `~/myforecast/forecast.yaml` file. In particular set:
 
    ```
    working_dir       : $(HOME)/myforecast                          # directory to work from, expects namelist.wps and namelist.input to be here
    wrftools_dir      : $(HOME)/code/wrftools                       # location of local wrftools repository
    wps_dir           : $(HOME)/WPS                                 # location of WPS code
    wrf_dir           : $(HOME)/WRF                                 # location of WRF code 
    ```
    
8. Run the forecast:
 
    ```
    $> cd ~/myforecast
    $> python run_forecast.py --config=forecast.yaml
    ```

Outputs will be created in:

    ~/myforecast/wps     # all of the logs associated with WPS
    ~/myforecast/wrf     # all of logs associated with WRF
    ~/myforecast/wrfout  # final wrfout files
    ~/myforcecast/plots  # output plots
    ~/myforecast/tseries # interpolated time-series

 

# More detailed docs 
     
## Dependencies

The following external tools are required. All are findable via your favourite search engine.

* WRF        - obviously
* WPS        - ditto
* gribmaster - fetches external boundary conditions 
* NCL        - for visualisation and time-series extraction
* NCO        - needed for adding metadata and compression (compiled with netCDF4 support)

### Python dependecies

Despite trying to reduce the python dependencies to a bare minimimum, 
there are still some modules which are not included with a standard
python installation. These are:

* numpy  - everyone has this, right?
* pyyaml - needed if yaml is used for config files (recommended)
* docopt - intelligent parsing of command-line arguments
* netCDF4 - not needed for core functionality, but used in the `extract` stage


## Usage

Basic usage is:

    $> python run_forecast.py --config=<config_file>

Any configuration options can also be specified on the command-line, where they will override 
those in the config file e.g.

    $> python run_forecast.py --config=<config_file> --log.level=debug

See [example/forecast.yaml](example/forecast.yaml) for an explanation of options

## Modularity

The forecast process is divided into stages. 
There are currently the following stages:

* fetch          - a thin wrapper around gribmaster, fetches boundary conditions
* prepare        - ensures correct files present, does some linking, updates namelist files
* simulate       - runs WPS and WRF
* post           - adds metadata, compresses files
* visualise      - calls NCL with specified scripts. Note the English (i.e. correct ;) spelling
* extract        - extracts time-series of variables at specified locations, relies on NCL
* finalise       - removes files, transfers locally, archive etc. 
* dispatch       - send out emails, plots etc


Each component has an associated python module in the form of a single file within the `wrftools/wrftools` directory, 
i.e. everything to do with the fetch stage is defined within `wrftools/fetch.py`. 
Each stage has an associated boolean option within the config file which turns that stage on or off
e.g. to run the fetch stage, set `fetch : true` in the config file, or use `--fetch=true` at the command line. 

## Configuration

For explanation of configuration options, see [example/forecast.yaml](example/forecast.yaml).

Some options in the configution. e.g. start time, maximum number of nests, 
** will override settings in the namelist.input and namelist.wps files **

Configuration is done via a config file, alhough options can also be overridden 
at the command line. json and yaml formats are understood. json has the advantage
that a parser is included in standard python distributions. 
However, I prefer YAML since the syntax is clearer, and the files can be commented.
JSON will not be supported in future, unless there is a great need for it.

Within a config file, environment variables can be specified accessed using `$(var)`.
Local variables defined elsewhere in tht config file can be specified  using `%(var)`.
If the variable in `${}` or `%()` is not defined within the current environments,
it will not be expanded. This is not part of standard yaml or json!

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




Additional configuration files can be included using %[file.json] or %[file.yaml]. Wherever the 
directive is found, the target file will be parsed as a dictionary, and placed into the parent scope. 



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
 

## Visualisation / interface with NCL

NCL is used as the primary visualisation and extraction tool.
Communication with NCL is done via a automatically written an options file, which is a fragment of ncl code, and setting the
enviroment variable `$NCL_OPT_FILE` to point to this file. 

The ncl options file defines the following variables:

    ncl_in_file   = ; input file to process
    ncl_out_dir   = ; directory for outputs (multiple files)
    ncl_out_file  = ; filename of output (single files)
    ncl_out_type  = ; output type (png, pdf, nc)
    ncl_loc_file  = ; csv file with latitude and longitude of points
    ncl_extract_heights  = ; heights to interpolate to

Thus, if you want to write an NCL script which 'plugs in' to this, just use put:
    
      load "$NCL_OPT_FILE"

in the script, and the above variables shoudl magically be defined.


 
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
