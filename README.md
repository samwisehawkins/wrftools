wrftools
--------

**The master branch has changed significantly** and now depends on a scheduler such 
as the Sun Grid Engine.  This makes it much easier to run large historical simulations. 
A branch corresponding to the old master is available as the synchronous branch.

### What is it?

A framework for running WRF simulations.

It is designed to be flexible and extendable. There are some tools out there
which run WRF, but they are not easily modified. This is designed to provide 
a framework which is easily customised and modified. 

Not yet python 3 compatible. 

### Install

It relies on two other custom python packages. Grab these and install as you usually would.
(If you are working on Maestro, these are already installed)
   
    $>git clone https://github.com/samwisehawkins/confighelper.git
    $>python confighelper/setup.py install

    $>git clone https://github.com/samwisehawkins/loghelper.git
    $>python loghelper/setup.py install

Get the main repository    
    
    $>git clone https://github.com/samwisehawkins/wrftools.git


### Quick start

There are three main scripts:

* [init.py](init.py) intialises a base directory
* [prepare.py](prepare.py) prepare simulations in seperate directories
* [submit.py](submit.py) submit simulations them to the scheduler

Assuming you have wrftools repository and the dependencies installed.

    mkdir myforecast
    cp /some/path/namelist.wps ./
    cp /some/path/namelist.input ./
    cp wrftools/config/init.yaml ./
    python wrftools/init.py --config=init.yaml
    python prepare.py --config=prepare.yaml
    ls -l      # ooh, look at all those simulations waiting to go!
    python submit.py --config=submit.yaml
    
    
### Documentation

See [docs/documentation.md](documentation) for more details


 
----------
Author 
Sam Hawkins
samwisehawkins@gmail.com
---------
