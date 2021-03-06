def skullstrip_flash(input, path_output, name_output, min_val=100, max_val=1000, flood_fill=False,
                     cleanup=False):
    """
    This function computes a brain mask for a partial coverage T2*-weighted anatomical image. The 
    mask is used to remove the sagittal sinus during segmentation. Thus, the latest echo should be 
    used here to get the largest difference between venous and tissue compartments. The brain mask 
    is generated by a simple thresholding operation. An intenstiy gradient in posterior-anterior 
    direction is considered by thresholding all slices independently. The threshold value is 
    computed from the intensity histogram of each slice by getting the minimum of the histogram 
    within a predefined range.
    Inputs:
        *input: input path of T2*-weighted anatomy.
        *path_output: path where output is saved.
        *name_output: basename of output file.
        *min_val: minimum threshold of intensity histogram.
        *max_val: maximum threshold of intenstiy histogram.
        *flood_fill: apply flood filling of binary mask (boolean).
        *cleanup: delete intermediate files (boolean).
        
    created by Daniel Haenelt
    Date created: 05-05-2019          
    Last modified: 05-05-2019
    """
    import os
    import numpy as np
    import nibabel as nb
    from nipype.interfaces.ants import N4BiasFieldCorrection
    from scipy.signal import argrelextrema
    from scipy.ndimage.morphology import binary_fill_holes

    # prepare path and filename
    path = os.path.dirname(input)
    file = os.path.splitext(os.path.basename(input))[0]

    # bias field correction
    n4 = N4BiasFieldCorrection()
    n4.inputs.dimension = 3
    n4.inputs.input_image = os.path.join(path,file+".nii")
    n4.inputs.bias_image = os.path.join(path,"n4bias.nii")
    n4.inputs.output_image = os.path.join(path,"b"+file+".nii")
    n4.run()

    # load input data
    mask = nb.load(os.path.join(path,"b"+file+".nii"))
    mask_array = mask.get_fdata()

    # loop through slices
    for i in range(np.shape(mask_array)[2]):

        # load slice
        temp = np.reshape(mask_array[:,:,i],np.size(mask_array[:,:,i]))
        
        # get histogram
        bin, edge = np.histogram(temp,100)
        edge = edge[:-1]
    
        # find local minimum within defined range
        bin_min = argrelextrema(bin, np.less)
        edge_min = edge[bin_min]
    
        edge_min[edge_min < min_val] = 0
        edge_min[edge_min > max_val] = 0
        edge_min[edge_min == 0] = np.nan
        edge_min = np.nanmin(edge_min)
        
        # mask image
        mask_array[:,:,i][mask_array[:,:,i] < edge_min] = 0
        mask_array[:,:,i][mask_array[:,:,i] != 0] = 1

    # flood filling on brain mask
    if flood_fill:
        mask_array = binary_fill_holes(mask_array, structure=np.ones((2,2,2)))

    # write output
    output = nb.Nifti1Image(mask_array,mask.affine,mask.header)
    nb.save(output,os.path.join(path_output,name_output+"_mask.nii"))
    
    # clean intermediate files
    if cleanup:
        os.remove(os.path.join(path,"n4bias.nii"))
        os.remove(os.path.join(path,"b"+file+".nii"))