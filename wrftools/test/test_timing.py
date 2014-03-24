import wrftools
import sys


config   = wrftools.read_namelist(sys.argv[1]).settings

base_dir   = config['base_dir']
domain     = config['domain']
domain_dir = '%s/%s' % (base_dir, domain)
config['domain_dir'] = domain_dir                 # domain directory

wrftools.create_logger(config)
logger = wrftools.get_logger()
logger.info('testing timing')
wrftools.timing(config)
