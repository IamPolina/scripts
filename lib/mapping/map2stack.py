def map2stack(file_data, file_grid, sigma, path_output):
    """
    map2stack

    This script allows you to sample surface data to a patch defined on a regular grid. If multiple 
    data files are given in a list, all grids are stacked together.
    Inputs:
        *file_data: filename list of data.
        *file_grid: filename of grid coordinate mapping.
        *sigma: standard deviation of Gaussian kernel.
        *path_output: path where output is saved.

    created by Daniel Haenelt
    Date created: 01-11-2018             
    Last modified: 18-02-2019
    """
    import os
    import numpy as np
    import nibabel as nb
    from scipy.ndimage.filters import gaussian_filter

    # make output folder
    if not os.path.exists(path_output):
        os.mkdir(path_output)

    # load data
    grid_img = nb.load(file_grid)
    grid_array = grid_img.get_fdata()

    # dim
    x = grid_img.header["dim"][1]
    y = grid_img.header["dim"][2]
    z = len(file_data)
    
    # sample data onto grid
    stack_array = np.zeros((x,y,z))
    for i in range(z):
    
        # load data
        data_img = nb.load(file_data[i])
        data_array = data_img.get_fdata()
    
        # map to stack
        for j in range(x):
            for k in range(y):
                if grid_array[j,k] != 0:
                    stack_array[j,k,i] = data_array[grid_array[j,k].astype(int)]
            
        # gaussian filter (opt)
        if sigma != 0:
            order = 0
            mode = "reflect"
            truncate = 4.0
            for i in range(np.size(stack_array,2)):
                stack_array[:,:,i] = gaussian_filter(stack_array[:,:,i],
                           sigma=sigma,
                           order=order,
                           mode=mode,
                           truncate=truncate)

    # write output data
    filenameOUT = os.path.join(path_output,os.path.splitext(os.path.basename(file_data[0]))[0]+"_sigma"+str(sigma)+"_grid.nii")
    output = nb.Nifti1Image(stack_array, grid_img.affine, grid_img.header)
    nb.save(output,filenameOUT)
