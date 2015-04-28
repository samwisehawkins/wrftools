import sys, os
# this is an ugly hack, but it works
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wrftools'))
import namelist as nl


def main():
    args = sys.argv[1:]
    namelist_wps = args[0]
    namelist_input = args[1]
    sync_namelists(namelist_wps, namelist_input)
    

def sync_namelists(namelist_wps, namelist_input):
    """ Synchronises the domain definition sections between 
    namelist.wps and namelist.input"""
    wps = nl.read_namelist(namelist_wps)
    inp = nl.read_namelist(namelist_input)
    
    #
    # Sync all the settings which need to be synced
    #
    for setting in ['max_dom', 'e_we', 'e_sn', 'i_parent_start', 'j_parent_start', 'parent_grid_ratio']:
        val = wps.settings[setting]
        inp.update(setting, val)
    inp.to_file(namelist_input)
    
if __name__=="__main__":
    main()