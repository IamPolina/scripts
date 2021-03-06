def mesh_sampling(surf_in, vol_in, source2target_in, path_output, r=[0.4,0.4,0.4], 
                  interpolation="Cu", cleanup=True):
    """
    This function samples data onto a surface mesh. Optionally, the volume can be upsampled and a
    coordinate mapping can be applied to transform the surface mesh to the space of the input 
    volume.
    Inputs:
        *surf_in: filename of input surface mesh.
        *vol_in: filename of input volume from which data is sampled.
        *source2target_in: source to target coordinate mapping.
        *path_output: path where output is written.
        *r: destination voxel size after upsampling (performed if not None).
        *interpolation: interpolation method for upsampling of file from which data is sampled.
        *cleanup: remove intermediate files.
       
    created by Daniel Haenelt
    Date created: 24-06-2020        
    Last modified: 24-06-2020
    """
    import os
    import numpy as np
    import nibabel as nb
    import shutil as sh
    from sh import gunzip
    from lib.io.get_filename import get_filename
    from lib.utils.upsample_volume import upsample_volume
    from lib.surface.deform_surface import deform_surface
    from lib.mapping import map2surface

    # make output folder
    if not os.path.exists(path_output):
        os.makedirs(path_output)

    tmp = np.random.randint(0, 10, 5)
    tmp_string = ''.join(str(i) for i in tmp)
    path_temp = os.path.join(path_output, "temp_"+tmp_string)
    if not os.path.exists(path_temp):
        os.makedirs(path_temp)

    # get filenames
    _, hemi, name_mesh = get_filename(surf_in)
    name_mesh = name_mesh[1:]
    _, name_vol, _ = get_filename(vol_in)

    # set filenames
    vol_upsampled = os.path.join(path_temp, "vol_upsampled.nii")
    s2t_upsampled = os.path.join(path_temp, "s2t_upsampled.nii")

    # upsample volumes and rescale cmap
    if r:
        upsample_volume(vol_in, vol_upsampled, dxyz=r, rmode=interpolation)
        upsample_volume(source2target_in, s2t_upsampled, dxyz=r, rmode="Linear")
        
        # rescale cmap
        dim = nb.load(vol_in).header["dim"][1:4] - 1
        dim_upsampled = nb.load(vol_upsampled).header["dim"][1:4] - 1
    
        cmap_s2t = nb.load(s2t_upsampled)
        cmap_s2t_array = cmap_s2t.get_fdata()    
        for i in range(3):
            cmap_s2t_array[:,:,:,i] = cmap_s2t_array[:,:,:,i] / dim[i] * dim_upsampled[i]
        
        cmap_s2t_upsampled = nb.Nifti1Image(cmap_s2t_array, cmap_s2t.affine, cmap_s2t.header)
        nb.save(cmap_s2t_upsampled, s2t_upsampled)
    else:
        _, _, ext = get_filename(vol_in)
        sh.copy(vol_in, os.path.join(path_temp, "vol_upsampled"+ext))
        if ext[-3:] == ".gz":
            gunzip(os.path.join(path_temp, "vol_upsampled"+ext))
            
        _, _, ext = get_filename(source2target_in)
        sh.copy(source2target_in, os.path.join(path_temp, "s2t_upsampled"+ext))
        if ext[-3:] == ".gz":
            gunzip(os.path.join(path_temp, "s2t_upsampled"+ext))
        
    # deform mesh
    deform_surface(input_surf=surf_in,
                   input_orig=s2t_upsampled,
                   input_deform=s2t_upsampled,
                   input_target=vol_upsampled,
                   hemi=hemi,
                   path_output=path_temp,
                   input_mask=None,
                   interp_method="trilinear",
                   smooth_iter=0,
                   flip_faces=False,
                   cleanup=True)
    
    # do mapping
    map2surface(input_surf=os.path.join(path_temp, hemi+"."+name_mesh+"_def"),
                input_vol=vol_upsampled,
                hemi=hemi, 
                path_output=path_temp,
                input_white=None, 
                input_ind=None, 
                cleanup=True)
    
    # rename output surface
    os.rename(os.path.join(path_temp, hemi+".vol_upsampled_"+name_mesh+"_def_def.mgh"),
              os.path.join(path_output, hemi+"."+name_vol+"_"+name_mesh+".mgh"))
    
    # delete intermediate files
    if cleanup:
        sh.rmtree(path_temp, ignore_errors=True)