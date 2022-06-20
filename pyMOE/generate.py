####generate.py 

#import the gds operations from the gds_klops file 
from pyMOE.gds_klops import * 
import numpy as np 
from matplotlib import pyplot as plt
import cv2 

import pyMOE.sag_functions as sag

from pyMOE.aperture import Aperture



def create_empty_aperture(xmin, xmax, N_x, ymin, ymax, N_y):
    """
    Creates an empty aperture max of the mesh dimensions provided
    
    xmin, xmax: range for x 
    N_x: number of x points
    ymin, ymax: range for y 
    N_y: number of y points
    
    Returns:
    mask: empty Aperture
    """
    x = np.linspace(xmin, xmax, N_x)
    y = np.linspace(ymin, ymax, N_y)
    
    return Aperture(x,y)

def create_empty_aperture_from_aperture(aperture):
    """
    Creates an empty aperture with the same spatial dimensions of the given aperture
    
    Args:
        aperture: aperture
    Returns:
        aperture: empty Aperture of same spatial dimensions
    """
    assert type(aperture) is Aperture, "aperture must be of type Aperture"


    return Aperture(aperture.x, aperture.y)



def create_aperture_from_array(array, pixel_size, center=False):
    """
    Creates an aperture from the given array, where each pixel is of
    pixel_size

    Args:
        array: 2D numpy array of a mask
        pixel_size: absolute value for each pixel
        center: if True, will center the image at the origin
            
    Returns:
        aperture: aperture with the mask inserted
    """
    
    assert (isinstance(array, np.ndarray)) and (len(array.shape)==2), "Array must be 2D numpy array "
    assert isinstance(pixel_size, (int, float)), "pixel_size must be a scalar"
    shape = array.shape
    N_x, N_y = shape
    max_x = N_x*pixel_size
    max_y = N_y*pixel_size
    x = np.linspace(0, max_x, N_x, endpoint=False)
    y = np.linspace(0, max_y, N_y, endpoint=False)
    
    if center:
        x = x-np.mean(x)
        y = x-np.mean(y)
    aperture = Aperture(x,y)
    aperture.aperture = array
      
    return aperture
    





def circular_aperture(aperture, radius, center=(0,0)):
    """    
    Updates aperture and returns 2D circular aperture mask 
    
    Args: 
        aperture: mask of type Aperture
        radius: radius of the circle aperture
        center: default (x0=0, y0=0) center of circle
        
    Returns:
        aperture: aperture with circular amplitude
    """

    assert type(aperture) is Aperture, "aperture must be of type Aperture"
    assert radius is not None

    x0,y0 = center
    maskcir = np.zeros(aperture.shape)
            

    (xc, yc) = aperture.XX, aperture.YY
    #definition of the circular aperture 
    rc = np.sqrt((xc-x0)**2 + (yc-y0)**2)
    maskcir[np.where(rc<radius)] = 1


    aperture.aperture = maskcir
    return aperture

def rectangular_aperture(aperture, width, height, corner=None, center=None):
    """    
    Updates aperture and returns 2D rectangular aperture mask 
    
    Args: 
        aperture: aperture of type Aperture
        width, height:  width and height of the rectangle
        corner: if given, sets the lower left corner of the rectangle
        center: if given, sets the center of the rectangle
        
    Returns:
        aperture: aperture with rectangular amplitude
    """
    
    assert type(aperture) is Aperture, "aperture must be of type Aperture"

    
    if corner is not None:
        assert (type(corner)==tuple) and (len(corner) == 2)
        x0,y0 = corner
    if center is not None:
        assert (type(center)==tuple) and (len(center) == 2)
        xc, yc = center
        x0 = xc-width/2
        y0 = yc-height/2
    if (corner is None) and (center is None):
        xc = np.mean(aperture.x)
        yc = np.mean(aperture.y)
        
        x0 = xc-width/2
        y0 = yc-height/2
        
    mask = np.zeros(aperture.shape)
    mask[np.where((aperture.XX>=x0)&(aperture.XX<=x0+width)& (aperture.YY>=y0)&(aperture.YY<=y0+height))] = 1
    
    aperture.aperture = mask
    return aperture
    




def arbitrary_aperture_function(aperture, function, center=(0,0), **function_args):
    """    
    Updates aperture and returns phase mask calculated based on function
    
    Args: 
        aperture: mask of type Aperture
        function: function to calculate the phase on 
        **function_args: additional arguments to pass onto the function
    Returns:
        aperture: aperture with fresnel phase
    """

    assert type(aperture) is Aperture, "aperture must be of type Aperture"
    assert callable(function), "provided function must be callable"

    x0,y0 = center
    

    #calculate the fresnel complex phase 
    output = function(aperture.XX-x0, aperture.YY-y0, **function_args)

    aperture.aperture = output
    
    return aperture

def truncate_aperture_radius(aperture, radius, center=(0,0), truncate_value=0):
    """
    Truncates the aperture to inside the circle of radius at center
    
    Args:
        aperture: mask to be truncated
        radius: radius to select the region
        center: center points tuple of the circle
        truncate_value: value to truncate the mask, by default 0 
    
    Returns:
        aperture
    """
    
    
    x0,y0 = center
    rc = np.sqrt((aperture.XX-x0)**2 + (aperture.YY-y0)**2)
    
    array = aperture.aperture
    array[rc>radius] = truncate_value
    aperture.aperture = array
    
    return aperture


def fresnel_phase(aperture, focal_length, wavelength, radius=None, center=(0,0)):
    """    
    Updates aperture and returns Fresnel phase mask
    
    Args: 
        aperture: mask of type Aperture
        focal_length: design focal length
        wavelength: design wavelength
        radius: if defined, truncates the fresnel phase to inside this radius
        
    Returns:
        aperture: aperture with fresnel phase
    """

    assert type(aperture) is Aperture, "aperture must be of type Aperture"
    assert focal_length is not None
    assert wavelength is not None

    aperture = arbitrary_aperture_function(aperture, sag.fresnel_lens_phase, 
    center=center, focal_length=focal_length, wavelength=wavelength)

    if radius is not None:
        aperture = truncate_aperture_radius(aperture, radius, center=center)


    return aperture



def fresnel_zone_plate_aperture(aperture, focal_length, wavelength, radius=None, center=(0,0)):
    """    
    Updates aperture and returns Fresnel zone plate aperture
    
    Args: 
        aperture: mask of type Aperture
        focal_length: design focal length
        wavelength: design wavelength
        radius: if defined, truncates the fresnel phase to inside this radius
        
    Returns:
        aperture: aperture with fresnel zone plate
    """

    assert type(aperture) is Aperture, "aperture must be of type Aperture"
    assert focal_length is not None
    assert wavelength is not None

    x0,y0 = center
    mask = np.zeros(aperture.shape)
    

    #definition of the circular aperture 
    rc = np.sqrt((aperture.XX-x0)**2 + (aperture.YY-y0)**2)
    
    #definition of the phase profile 
    fzp = np.exp(-1.0j*(focal_length-np.sqrt(focal_length**2 + rc**2))*(2*np.pi)/(wavelength))

    #Define the zones 
    fzp[np.where((np.angle(fzp)>-np.pi/2 )& (np.angle(fzp)<np.pi/2) )] = 0 

    i,j = fzp.shape 

    #final plateCurrent 
    fzp2 = np.ones((i,j)) 
    
    fzp_angle = np.angle(fzp)
    
    idx_array = (fzp_angle>=-np.pi/2) & (fzp_angle<=np.pi/2)
    fzp2[idx_array] = 0

    if radius is not None:
        fzp2[np.where(rc>radius)] = 1  
                 
    aperture.aperture = fzp2
    return aperture


# Aperture operations


def aperture_operation(aperture1, aperture2, operand):
    """Executes the operation on the apertures 1 and 2.
    Both apertures must have the same spatial distribution and shape.
    
    Args:
        aperture1: First Aperture
        aperture2: Second Aperture
        operand: numpy operand function to consider
        
    Returns:
        aperture: Aperture with result of operation
    """
    assert (type(aperture1) is Aperture) and type(aperture2) is Aperture, "aperture must be of type Aperture"
    assert type(operand) == np.ufunc, "operand must be a numpy function"

    assert np.all(aperture1.XX == aperture2.XX) and np.all(aperture1.YY == aperture2.YY), "Spatial dimensions of aperture1 and aperture2 must be the same"


    aperture3 = create_empty_aperture_from_aperture(aperture1)
    aperture3.aperture = operand(aperture1.aperture, aperture2.aperture)
    return aperture3


def aperture_add(aperture1, aperture2):
    """Adds two apertures"""
    return aperture_operation(aperture1, aperture2, np.add)


def aperture_subtract(aperture1, aperture2):
    """Subtracts two apertures"""
    return aperture_operation(aperture1, aperture2, np.subtract)

def aperture_multiply(aperture1, aperture2):
    """Multiply two apertures"""
    return aperture_operation(aperture1, aperture2, np.multiply)

    
def makegrid(npix, xsiz, ysiz): 
    """
    Creates a meshgrid of npix by npix in with arrays till xsiz and ysiz 

    Args: 
        npix = nr of pixels , by default the results 2D array is npix by npix 
        xsiz = size in x  
        ysiz = size in y 
    
    Returns:     
        Meshgrid (XX, YY) 

    """

    maskcir = np.zeros((npix,npix))
    xc1 = np.linspace(0, xsiz, npix)
    yc1 = np.linspace(0, ysiz, npix)
    (XX, YY ) = np.meshgrid(xc1,yc1)
    
    return (XX, YY )
    



def save_mask_plot(maskcir, xsiz, ysiz, filename):
    fig1 = plt.figure()
    figx = plt.imshow(maskcir, vmin=0, vmax=1,extent =[0,xsiz,0,ysiz], cmap=plt.get_cmap("Greys"))
    plt.axis('off')
    figx.axes.get_xaxis().set_visible(False)
    figx.axes.get_yaxis().set_visible(False)
    plt.savefig(filename, bbox_inches='tight', pad_inches = 0)
    plt.close(fig1)
    

##Code to create a gray scale with successive gray levels 
def create_scale(npixel, nsz, ngs): 
    """
    returns a 2D array with a scale of successive gray levels 
    npixel= nr of pixels 
    nsz = division in size 
    ngs = nr of gray levels 
    
    """
    
    scale_img = np.zeros((npixel,npixel,3), np.uint8)

    width = npixel 
    height = npixel 
    
    nsz = npixel/ngs 
    
    xdims = np.arange(0,width, nsz)
    
    xdist = 255/ngs
    xlevs = np.arange(0,255, xdist)
    print(xlevs)

    print(xdims)

    gslev = ngs

    xdimsint = np.array(xdims, dtype=int)
    xdimsround = np.round(xdimsint)

    for iw, wd in enumerate(xlevs):
        if iw == (len(xdims)-1): 
            break 
            
        gss =255 - np.round(wd)
        
        colorgray = np.uint8([[gss,gss,gss]])
        
        graycolor = cv2.cvtColor(colorgray, cv2.COLOR_GRAY2RGB)
        
        scale_img[:,xdimsround[iw]:xdimsround[iw+1]] = (int(graycolor[0][0][0]),int(graycolor[0][0][1]),int(graycolor[0][0][2]))      # (B, G, R)
        
    
    fig1 = plt.figure()
    plt.imshow(scale_img, vmin=0, vmax=255, cmap=plt.get_cmap("Greys"))
    plt.title("scaled")
 
    return scale_img
    

def fresnel_phase_mask(npix, foc, lda, xsiz, ysiz,n, filename=None, plotting=False ,prec = 1e-6, mpoints = 1e9, grid=None):
    """
    returns a Fresnel "phase mask" (2D array of the phase IN RADIANS)
    parameters: 
    npix = nr of pixels , by default the results 2D array is npix by npix 
    foc = focal length in um
    lda = wavelength in um 
    xsiz = size in x in um 
    ysiz = size in y in um
    n = number of gray levels 
    
    optional: 
    filename = string with mask output into GDS  (default None)
    plotting = True, shows the mask  (default False)
    prec = precision of the gdspy boolean operation  (default 1e-6)
    mpoints = max_points of the gdspy polygon (default 1e9)
    grid = 2D array with a meshgrid 
    
    Example of use: 
    fresnel_phase_mask(npix = 5000, \
                   foc = 5000,\
                   lda = 0.6328 ,\
                   xsiz = 500,\
                   ysiz =500,\
                   n=10,\
                   filename='fresnel_phase_mask.gds',\
                   plotting=True )   #Should take around ~30 s 
         
    """  

    #by default centered 
    xcmm =  0.5* xsiz
    ycmm =  0.5* ysiz 
    
    a = 0.5 * np.min([xsiz,ysiz])  #radius of the circular aperture 
    maskfres = np.ones((npix,npix))

            
    if grid is not None: 
        (xc, yc) = grid
    else: 
        xc1 = np.linspace(0, xsiz, npix)
        yc1 = np.linspace(0, ysiz, npix)
        (xc, yc) = np.meshgrid(xc1,yc1)

    
    
    #definition of the circular aperture 
    rc = np.sqrt((xc-xcmm)**2 + (yc-ycmm)**2)

    #calculate the fresnel complex phase 
    fresarray = lensfres(xc,yc,xcmm,ycmm,foc,lda)
    
    fresarray[np.where(rc>a)] = np.pi
    fresarray_rad = np.angle(fresarray)
    
    #make array with the z plane intersections  (n gray levels)
    zlevs = np.linspace(np.min(fresarray_rad), np.max(fresarray_rad), n+1)
    
    print(zlevs)

    if plotting == True: 
        plt.figure()
        plt.axis('equal')
        cs = plt.contourf(xc,yc,fresarray_rad, zlevs, cmap=plt.get_cmap("Greys"))
        plt.xlabel('x ($\mu$m)')
        plt.ylabel('y ($\mu$m)')
        plt.colorbar(label='Phase (rad)')
        plt.tight_layout()
    else: 
        cs = plt.contourf(xc,yc,fresarray_rad, zlevs, cmap=plt.get_cmap("Greys"))
      
    #possible improvement, pass this function as argument
    #lib1, cell1 = cell_wpol_gdspy_fast(cs, 'TOP', prec, mpoints)
    lib1, cell1 = cell_wpol_gdspy(cs, 'TOP', prec, mpoints)

    if filename is not None: 
        lib1.write_gds(filename)
        print("Saved the phase profile with " + str(len(zlevs)-1) +  " layers into the file " + filename)
        
    return fresarray_rad 




###ANY FUNCTION PHASE MASK 
def arbitrary_phase_mask(mode, npix, xsiz, ysiz, n, fname,*args,filename=None, plotting=False ,prec = 1e-6, mpoints = 1e9 , zlevs = [],grid=None, **kwargs):
    """
    returns a "phase mask" (2D array of the phase IN RADIANS) from arbitrary COMPLEX PHASE function fname  given as argument
    
    parameters: 
    mode = 'gdspyfast', 'gdspy', 'gdshelper'
    npix = nr of pixels (or points) , by default the results 2D array is npix by npix 
    xsiz = size in x in um 
    ysiz = size in y in um
    n = number of gray levels
    fname = function name (e.g. lensfres(x,y,x0,y0, args) , where args will be given as *args)
    *args = arguments fname, excluding the [x,y,x0,y0] params
    
    optional: 
    filename = string with mask output into GDS  (default None)
    plotting = True, shows the mask  (default False)
    prec = precision of the gdspy boolean operation  (default 1e-6 um)
    mpoints = max_points of the gdspy polygon (default 1e9 points)
    zlevs   = array of the phase levels 
    grid = 2D array with a meshgrid 
    
    Examples of use: #Should take around ~30 s for any of these 
    arbitrary_phase_mask(5000, 500,500, 10,\
           lensfres, fo=5000, lda=0.6328, \
           filename="fresnel_phase_plate.gds", plotting=True ,prec = 1e-6, mpoints = 1e9 )
           
    arbitrary_phase_mask(5000, 500,500, 60,\
           spiral, L=1, \
           filename="spiral_phase_plate.gds", plotting=True ,prec = 1e-12, mpoints = 1e9 )
         
    """  

    #by default centered 
    xcmm =  0.5* xsiz
    ycmm =  0.5* ysiz 
    lib1 = 0 
    
    maskfres = np.ones((npix,npix))

            
    if grid is not None: 
        (xc, yc) = grid
    else: 
        xc1 = np.linspace(0, xsiz, npix)
        yc1 = np.linspace(0, ysiz, npix)
        (xc, yc) = np.meshgrid(xc1,yc1)


    #calculate the complex phase  fname function  
    farray = fname(xc,yc,xcmm,ycmm,*args, **kwargs)
    
    
    #make array with the z plane intersections  (n gray levels)
    if zlevs == []: 
        zlevs = np.linspace(np.min(farray), np.max(farray), n+1)
        #print(zlevs)

    if plotting == True: 
        plt.figure()
        plt.axis('equal')
        cs = plt.contourf(xc,yc,farray, zlevs, cmap=plt.get_cmap("Greys"))
        plt.xlabel('x ($\mu$m)')
        plt.ylabel('y ($\mu$m)')
        plt.colorbar(label='Phase (rad)')
        plt.tight_layout()
      
    #possible improvement, pass this function as argument
    if mode == 'gdspyfast': 
        lib1, cell1 = cell_wpol_gdspy_fast(cs, 'TOP', prec, mpoints)
        cell2 = None 
        multpol = None 
        
    if mode == 'gdspy': 
        lib1, cell1 = cell_wpol_gdspy(cs, 'TOP', prec, mpoints)
        cell2 = None 
        multpol = None 
        
    if mode == 'gdshelper': 
        cell2, multpol = cell_wpol(cs, 'TOP')

    #option for gdspy lib use 
    if lib1 and filename is not None: 
        lib1.write_gds(filename)
        print("Saved the phase profile with " + str(n) +  " layers into the file " + filename)
    
    #option for gdshelpers lib use 
    if cell2 and filename is not None: 
        cell2.save(filename)
        print("Saved the phase profile with " + str(n) +  " layers into the file " + filename)
    
    return farray_rad 





###ANY FUNCTION PHASE MASK 
def arbitrary_multilayer_mask(mode, npix, xsiz, ysiz, n, fname,*args,filename=None, plotting=False ,prec = 1e-6, mpoints = 1e9 , zlevs = [],grid=None, **kwargs):
    """
    returns a "contour" mask of the arbitrary fname function 
    
    parameters: 
    mode = 'gdspyfast', 'gdspy', 'gdshelper'
    npix = nr of pixels (or points) , by default the results 2D array is npix by npix 
    xsiz = size in x in um 
    ysiz = size in y in um
    n = number of gray levels
    fname = function name (e.g. lensfres(x,y,x0,y0, args) , where args will be given as *args)
    *args = arguments fname, excluding the [x,y,x0,y0] params
    
    optional: 
    filename = string with mask output into GDS  (default None)
    plotting = True, shows the mask  (default False)
    prec = precision of the gdspy boolean operation  (default 1e-6 um)
    mpoints = max_points of the gdspy polygon (default 1e9 points)
    zlevs   = array of the phase levels 
    grid = 2D array with a meshgrid 
    
    Examples of use: #Should take around ~30 s for any of these 
    arbitrary_phase_mask(5000, 500,500, 10,\
           lensfres, fo=5000, lda=0.6328, \
           filename="fresnel_phase_plate.gds", plotting=True ,prec = 1e-6, mpoints = 1e9 )
           
    arbitrary_phase_mask(5000, 500,500, 60,\
           spiral, L=1, \
           filename="spiral_phase_plate.gds", plotting=True ,prec = 1e-12, mpoints = 1e9 )
         
    """  

    #by default centered 
    xcmm =  0.5* xsiz
    ycmm =  0.5* ysiz 
    lib1 = 0 
    
    maskfres = np.ones((npix,npix))

            
    if grid is not None: 
        (xc, yc) = grid
    else: 
        xc1 = np.linspace(0, xsiz, npix)
        yc1 = np.linspace(0, ysiz, npix)
        (xc, yc) = np.meshgrid(xc1,yc1)


    #calculate the complex phase  fname function  
    farray = fname(xc,yc,xcmm,ycmm,*args, **kwargs)
    
    
    #make array with the z plane intersections  (n gray levels)
    if zlevs == []: 
        zlevs = np.linspace(np.min(farray), np.max(farray), n+1)
        #print(zlevs)

    if plotting == True: 
        plt.figure()
        plt.axis('equal')
        cs = plt.contourf(xc,yc,farray, zlevs, cmap=plt.get_cmap("Greys"))
        plt.xlabel('x ($\mu$m)')
        plt.ylabel('y ($\mu$m)')
        plt.colorbar(label='Phase (rad)')
        plt.tight_layout()
      
    #possible improvement, pass this function as argument
    if mode == 'gdspyfast': 
        lib1, cell1 = cell_wpol_gdspy_fast(cs, 'TOP', prec, mpoints)
        cell2 = None 
        multpol = None 
        
    if mode == 'gdspy': 
        lib1, cell1 = cell_wpol_gdspy(cs, 'TOP', prec, mpoints)
        cell2 = None 
        multpol = None 
        
    if mode == 'gdshelper': 
        cell2, multpol = cell_wpol(cs, 'TOP')

    #option for gdspy lib use 
    if lib1 and filename is not None: 
        lib1.write_gds(filename)
        print("Saved the phase profile with " + str(n) +  " layers into the file " + filename)
    
    #option for gdshelpers lib use 
    if cell2 and filename is not None: 
        cell2.save(filename)
        print("Saved the phase profile with " + str(n) +  " layers into the file " + filename)
    
    return farray
    
    
  
####Function that defines a Fresnel Zone Plate mask 
def fzp_mask(npix, foc, lda, xsiz, ysiz, filename, plotting=False, grid=None ):
    """
    returns a fresnel zone plate (as a numpy 2D array)
    npix = nr of pixels 
    foc = focal length in um
    lda = wavelength in um 
    xsiz = size in x in um 
    ysiz = size in y in um 
    filename = string with mask image name 'image.png'
    
    Optional: 
    plotting=True, shows the mask 
    grid = 2D array with a meshgrid 
    
    Example of use: 
    
    fzp_mask(npix = 50,\
         foc = 5000 ,\
         lda = 0.6328 ,\
         xsiz = 500, \
         ysiz = 500, \
         filename = 'fresnel.png', \
         plotting=True )
         
    """

    #by default centered
    xcmm =  0.5* xsiz
    ycmm =  0.5* ysiz 

    a = 0.5 * np.min([xsiz,ysiz])  #radius of the circular aperture 
    maskfres = np.ones((npix,npix))

            
    if grid is not None: 
        (xc, yc) = grid
    else: 
        xc1 = np.linspace(0, xsiz, npix)
        yc1 = np.linspace(0, ysiz, npix)
        (xc, yc) = np.meshgrid(xc1,yc1)


    #calculate the complex phase  fname function  
    farray = fname(xc,yc,xcmm,ycmm,*args, **kwargs)
    
    
    #make array with the z plane intersections  (n gray levels)
    if zlevs == []: 
        zlevs = np.linspace(np.min(farray), np.max(farray), n+1)
        #print(zlevs)

    if plotting == True: 
        plt.figure()
        plt.axis('equal')
        cs = plt.contourf(xc,yc,farray, zlevs, cmap=plt.get_cmap("Greys"))
        plt.xlabel('x ($\mu$m)')
        plt.ylabel('y ($\mu$m)')
        plt.colorbar(label='Phase (rad)')
        plt.tight_layout()
      
    #possible improvement, pass this function as argument
    if mode == 'gdspyfast': 
        lib1, cell1 = cell_wpol_gdspy_fast(cs, 'TOP', prec, mpoints)
        cell2 = None 
        multpol = None 
        
    if mode == 'gdspy': 
        lib1, cell1 = cell_wpol_gdspy(cs, 'TOP', prec, mpoints)
        cell2 = None 
        multpol = None 
        
    if mode == 'gdshelper': 
        cell2, multpol = cell_wpol(cs, 'TOP')

    #option for gdspy lib use 
    if lib1 and filename is not None: 
        lib1.write_gds(filename)
        print("Saved the phase profile with " + str(n) +  " layers into the file " + filename)
    
    #option for gdshelpers lib use 
    if cell2 and filename is not None: 
        cell2.save(filename)
        print("Saved the phase profile with " + str(n) +  " layers into the file " + filename)
    
    return farray