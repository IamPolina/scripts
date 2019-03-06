"""
ALFF

The purpose of the following script is to compute ALFF and fALFF for a resting-state time series. 
The time series is baseline corrected and nuisance regressors are taken either from mean WM and
CSF masks or based on biopac recordings. Optionally, no nuisance regression is performed.

Before running the script, login to queen via ssh and set the freesurfer, ANTS and AFNI environments 
by calling FREESURFER, ANTSENV and AFNI in the terminal.

created by Daniel Haenelt
Date created: 02-03-2019
Last modified: 03-03-2019
"""
import os
import nibabel as nb
from lib.preprocessing.get_nuisance_mask import get_nuisance_mask
from lib.preprocessing.get_nuisance_regressor import get_nuisance_regressor
from lib.processing.get_alff import get_alff

# input
anatomy = "/data/pt_01880/V2STRIPES/p6/anatomy/freesurfer/mri/orig.mgz" # T1w full brain anatomy
function = "/data/pt_01880/V2STRIPES/p6/resting_state/udata.nii" # baseline uncorrected
deformation = "/data/pt_01880/V2STRIPES/p6/deformation/resting_state/orig2epi.nii.gz" # deformation ana -> epi
biopac_input = "/data/pt_01880/V2STRIPES/p6/resting_state/logfiles/OA7T190121.mat"
path_output = "/data/pt_01880/V2STRIPES/p6/resting_state/alff_biopac"

# add path
pathSPM = "/data/pt_01880/source/spm12"
pathLIB = "/home/raid2/haenelt/projects/scripts/lib/preprocessing"

# parameters
TR = 2 # repetition time in s
cutoff_highpass = 120 # cutoff frequency for baseline correction in 1/Hz
nerode_wm = 1 # number of wm mask eroding iterations
nerode_csf = 1 # number of csf mask eroding iterations
hp_freq = 0.01 # highpass cutoff frequency (bandpass filter) in Hz
lp_freq = 0.08 # lowpass cutoff frequency (bandpass filter) in Hz

# analysis type
nuisance_regression = True
segmentation = False
biopac = True
cleanup = True

""" do not edit below """

# make output folder
if not os.path.exists(path_output):
    os.mkdir(path_output)

# get path and filenames
path = os.path.dirname(function)
file = os.path.basename(function)
bfile = "b" + file # filename of baseline corrected time series
rfile = "r" + file # filename of residual time series

# physiological noise regression
if nuisance_regression:
    
    # baseline correction
    previous_cwd = os.getcwd()
    os.chdir(pathLIB)
    os.system("matlab" + \
              " -nodisplay -nodesktop -r " + \
              "\"baseline_correction(\'{0}\', {1}, {2}, \'{3}\'); exit;\"". \
              format(function, TR, cutoff_highpass, pathSPM))
    os.chdir(previous_cwd)

    if biopac:
        
        # get biopac regressors
        previous_cwd = os.getcwd()
        os.chdir(pathLIB)
        os.system("matlab" + \
                  " -nodisplay -nodesktop -r " + \
                  "\"get_biopac_regressor(\'{0}\', \'{1}\', \'{2}\', \'{3}\', {4}); exit;\"". \
                  format(os.path.join(path,bfile), biopac_input, pathSPM, path_output, TR))
        os.chdir(previous_cwd)
    
    else:

        # get wm and csf mask
        get_nuisance_mask(anatomy, pathSPM, deformation, path_output, 
                          nerode_wm, nerode_csf, segmentation, cleanup)
    
        # set mask to zero where function is equal to zero
        func_array = nb.load(function).get_fdata()
        func_array = func_array[:,:,:,0]
    
        wm = nb.load(os.path.join(path_output,"wm_mask.nii.gz"))
        wm_array = wm.get_fdata()
        wm_array[func_array == 0] = 0
        output = nb.Nifti1Image(wm_array, wm.affine, wm.header)
        nb.save(output,os.path.join(path_output,"wm_mask.nii.gz"))

        csf = nb.load(os.path.join(path_output,"csf_mask.nii.gz"))
        csf_array = csf.get_fdata()
        csf_array[func_array == 0] = 0
        output = nb.Nifti1Image(csf_array, csf.affine, csf.header)
        nb.save(output,os.path.join(path_output,"csf_mask.nii.gz"))

        # get nuisance regressor
        os.chdir(previous_cwd) # change to existing path because of cleanup
        get_nuisance_regressor(os.path.join(path,bfile), 
                               os.path.join(path_output,"wm_mask.nii.gz"), 
                               os.path.join(path_output,"csf_mask.nii.gz"), 
                               path_output)
    
    # nuisance regression
    if cleanup:
        clean_glm = 1
    else:
        clean_glm = 0

    previous_cwd = os.getcwd()
    os.chdir(pathLIB)
    os.system("matlab" + \
              " -nodisplay -nodesktop -r " + \
              "\"regress_physio(\'{0}\', \'{1}\', \'{2}\', {3}, {4}, \'{5}\', {6}); exit;\"". \
              format(function, 
                     os.path.join(path_output,"nuisance_regressor.txt"), 
                     pathSPM, TR, cutoff_highpass, path_output, clean_glm))
    os.chdir(previous_cwd)

    # get alff    
    get_alff(os.path.join(path_output,rfile), TR, path_output, hp_freq, lp_freq, cleanup)
    
    # remove baseline corrected time series
    if cleanup:
        os.remove(os.path.join(path,bfile))

else:

    # get alff
    get_alff(function, TR, path_output, hp_freq, lp_freq, cleanup)