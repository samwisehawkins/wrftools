import sys
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
#import mpl_toolkits.basemap.pyproj as pyproj
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from netCDF4 import Dataset
import numpy as np
import subprocess
import os
#import layers


def main():
    outfile = '/home/slha/forecasting/local.png'
    dataset = Dataset(sys.argv[1], 'r')
    lcc = proj_from_wrf(dataset)
    
    webmc = ccrs.Mercator(min_latitude=-85.0511287798066,
                               max_latitude=85.0511287798066,
                               globe=ccrs.Globe(ellipse=None,
                                           semimajor_axis=6378137,
                                           semiminor_axis=6378137,
                                           nadgrids='@null'))
    
    
    lat = dataset.variables['XLAT']
    lon = dataset.variables['XLONG']
    u = dataset.variables['U']
    v = dataset.variables['V']
    
    
    
    spd = (u**2+v**2)**0.5

    # This will create an axis whose projection system is web mercartor i.e. EPSG:3857
    fig, ax, proj, extent = create_web_mercator(lat,lon, width=10)

    #ax.coastlines()
    ax.contourf(lon, lat, spd, transform=ccrs.PlateCarree())
    #plt.savefig(outfile, bbox_inches='tight')

    save_fig_as_layer(outfile, fig, "EPSG:3857", extent, img_dir="./img", opacity=0.7)


    
def get_img_size(filename):
    """reuturns the (width, height) of an image in 
    pixels via a system call to ImageMagick's identify"""
    cmd = "identify %s" % filename
    p = subprocess.Popen(["identify", filename], stdout=subprocess.PIPE)
    out, err = p.communicate()
    tokens= out.split()[2].split('x')
    return (int(tokens[0]), int(tokens[1]))
    
    
    

def trim(filename, suffix='.original', delta=50):
    """ trim whitespace from around an image via
    system call to imagemagick. filename will
    be replaced with trimmed version, but original 
    will be stored as filename.suffix. Raise exception if 
    the file sizes differ by more then delta % """
    
    
    tmp = '%s.tmp' % filename
    if os.path.exists(tmp):
        os.remove(tmp)
    
    size =  os.path.getsize(filename)
    cmd = "convert -trim +repage %s %s" %(filename, tmp)

    subprocess.call(cmd, shell=True)
    new_size = os.path.getsize(tmp)
    obs_delta = abs(size-new_size)*100.0/size
    assert (obs_delta<delta)
    
    cmd = "cp %s %s%s" % (filename, filename, suffix)
    subprocess.call(cmd, shell=True)
    cmd = "mv %s %s" %(tmp, filename)
    subprocess.call(cmd, shell=True)
    
    
    

def proj_from_wrf(ncfile):
    
    if ncfile.MAP_PROJ_CHAR == "Lambert Conformal":

    # from the docs
    #cartopy.crs.LambertConformal(central_longitude=-96.0, central_latitude=39.0, false_easting=0.0, false_northing=0.0, secant_latitudes=(33, 45), globe=None, cutoff=-30)[source]
    # central_longitude - The central longitude. Defaults to 0.
    # central_latitude - The central latitude. Defaults to 0.
    # false_easting - X offset from planar origin in metres.
    # Defaults to 0.
    # false_northing - Y offset from planar origin in metres.
    # Defaults to 0.
    # secant_latitudes - The two latitudes of secant intersection.
    # Defaults to (33, 45).
    # globe - A cartopy.crs.Globe.
    # If omitted, a default globe is created.
    # cutoff - Latitude of map cutoff.
    # The map extends to infinity opposite the central pole so we must cut off the map drawing before then. A value of 0 will draw half the globe. Defaults to -30.

        props = {'central_longitude' : ncfile.CEN_LON,
                 'central_latitude': ncfile.CEN_LAT,
                 'secant_latitudes': (ncfile.TRUELAT1,ncfile.TRUELAT2)}
                 
        print props
        proj = ccrs.LambertConformal(central_longitude=ncfile.CEN_LON,central_latitude=ncfile.CEN_LAT, secant_latitudes=(ncfile.TRUELAT1,ncfile.TRUELAT2))
        return proj

    
def create_web_mercator(lat,lon, width=10):
    """ create a figure and axis representing a 
    sub-region of a web-mercartor projection.

    Arguments
        lat -- array-like latitudes in (WGS1984) of source data used to determine extent
        lon -- array-like longitudes in (WGS1984) of source data used to determine extent
        
    Returns figure, axis, and extent"""

    # create projection objections for transorming points
    wgs84 = pyproj.Proj("+init=EPSG:4326")
    web_mct = pyproj.Proj("+init=EPSG:3857")
    
    #
    # This defines web-mercartor in cartopy. Note that the min and max 
    # latitudes and longitudes are the global min and max, not those of
    # the subregion
    # 
    proj = ccrs.Mercator(min_latitude=-85.0511287798066,
                               max_latitude=85.0511287798066,
                               globe=ccrs.Globe(ellipse=None,
                                           semimajor_axis=6378137,
                                           semiminor_axis=6378137,
                                           nadgrids='@null'))
    #
    # in case we need the extent of the image
    # should the extent be based on the converting the max/min latitude 
    # and longitude, or should we convert all lat andd lons, and find 
    # the resulting max/min of the transformed points?
    #
    llx,lly = pyproj.transform(wgs84, web_mct, np.min(lon), np.min(lat))
    urx, ury = pyproj.transform(wgs84, web_mct, np.max(lon), np.max(lat))

    # extent is left, bottom, right, top
    extent = [llx, lly, urx, ury]
    
    # calculate aspect ratio for transformed image
    aspect_ratio = float(urx-llx)/(ury-lly)
    height = width/aspect_ratio

    fig = plt.figure(figsize=(width, height))
    ax = plt.axes([0,0,1,1], projection=proj)
    ax.set_xlim(xmin=llx, xmax=urx)
    ax.set_ylim(ymin=lly, ymax=ury)
    return fig, ax, proj, extent
 
 
def replace_extension(filename, ext):
    """returns a path identical to filename, but with the final 
    extenstion replaced with ext"""
    tokens = filename.split('.')
    tokens[-1] = ext
    return '.'.join(tokens)
    
 
 
def save_fig_as_layer(filename, fig, projection, extent, img_dir=None, **kwargs):
    """ saves a figure as filename, and a corresponing
    .json file with information which can be used to 
    construct a OpenLayer3 StaticImage layer.
    Relies on a system call to identify to get the image size.
    
    Arguments:
        filename -- name of file to save
        fig      -- figure to save
        proj     -- epsg string namig projection
        extent   -- [left, bottom, right, top] in units of proj
        relative  -- encode relative path in json file
        kwarfs    -- optional properties will be put into the outer image"""

    save_fig_as_image(filename, fig)
    size = get_img_size(filename)
    print size
    

    json_name = replace_extension(filename, 'json')
    url =  img_dir+'/' + os.path.split(filename)[-1] if img_dir else filename
    
    
    imgstatic = layers.ImageStatic(url, size=size, extent=extent, projection=projection)
    image = layers.Image(imgstatic, kwargs)
    
    out = open(json_name, 'w')
    out.write(str(image))
    out.close()
 
 
def save_fig_as_image(filename,fig,**kwargs):
    """ Save a Matplotlib figure as an image without borders or frames.
        Hat tip to: http://robotics.usc.edu/~ampereir/wordpress/?p=626

        Args:
            filename (str): String that ends in .png etc.

            fig (Matplotlib figure instance): figure you want to save as the image
        
        Keyword Args:
            orig_size (tuple): width, height of the original image used to maintain 
            aspect ratio.

    """

    fig.patch.set_alpha(0)
    ax=fig.gca()
    ax.set_frame_on(False)
    ax.set_xticks([])
    ax.set_yticks([])
    plt.axis('off')
    fig.savefig(filename, transparent=True, bbox_inches='tight',pad_inches=0)
    
    #extent = fig.get_size_inches() * fig.dpi
    #print extent
 
    # ax.spines['right'].set_color('none')
    # ax.spines['left'].set_color('none')
    # ax.spines['top'].set_color('none')
    # ax.spines['bottom'].set_color('none')
    # turn off ticks
    # ax.xaxis.set_ticks_position('none')
    # ax.yaxis.set_ticks_position('none')
    # ax.xaxis.set_ticklabels([])
    # ax.yaxis.set_ticklabels([])

 
 

if 'main' in __name__:
    main()