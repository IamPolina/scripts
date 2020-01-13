"""
EPI <-> EPI

The purpose of the following script is to compute the deformation field for the registration 
between different epi time series. The script consists of the following steps:
    1. set output folder structure
    2. n4 correction epi
    3. clean ana (remove ceiling and normalise)
    4. mask epi
    5. antsreg
    6. apply deformations

At the moment, we perform antsreg on the unpeeled bias corrected source and target images.

Before running the script, login to queen via ssh and set the freesurfer and ANTS environments by 
calling FREESURFER and ANTSENV in the terminal.

created by Daniel Haenelt
Date created: 19-08-2019
Last modified: 12-01-2020
"""
import os
import shutil as sh
from nipype.interfaces.ants import N4BiasFieldCorrection
from nighres.registration import embedded_antsreg, apply_coordinate_mappings
from lib.registration.mask_ana import mask_ana
from lib.registration.mask_epi import mask_epi
from lib.registration.clean_ana import clean_ana

# input data
file_mean_epi_source = "/data/pt_01880/Experiment2_Rivalry/p3/localiser/diagnosis/mean_data.nii"
file_mean_epi_target = "/data/pt_01880/Experiment2_Rivalry/p3/odc/GE_EPI1/diagnosis/mean_data.nii"
file_t1 = "/data/pt_01880/Experiment2_Rivalry/p3/anatomy/S7_MP2RAGE_0p7_T1_Images_2.45.nii"
file_mask = "/data/pt_01880/Experiment2_Rivalry/p3/anatomy/freesurfer/mri/brain.finalsurfs.manedit.mgz"
path_output = "/data/pt_01880/Experiment2_Rivalry/p3/deformation/localiser"
cleanup = True

# parameters for epi skullstrip
niter_mask = 3
sigma_mask = 3

# parameters for syn 
run_rigid = True
rigid_iterations = 1000 
run_affine = False 
affine_iterations = 1000 
run_syn = True 
coarse_iterations = 50 
medium_iterations = 150 
fine_iterations = 100 
cost_function = 'CrossCorrelation' 
interpolation = 'Linear' 

""" do not edit below """

"""
set folder structure
"""
path_temp = os.path.join(path_output,"temp")
path_epi_source = os.path.join(path_temp,"epi_source")
path_epi_target = os.path.join(path_temp,"epi_target")
path_t1 = os.path.join(path_temp,"t1")
path_syn = os.path.join(path_temp,"syn")

if not os.path.exists(path_output):
    os.makedirs(path_output)

if not os.path.exists(path_temp):
    os.makedirs(path_temp)

if not os.path.exists(path_epi_source):
    os.makedirs(path_epi_source)

if not os.path.exists(path_epi_target):
    os.makedirs(path_epi_target)

if not os.path.exists(path_t1):
    os.makedirs(path_t1)

if not os.path.exists(path_syn):
    os.makedirs(path_syn)

# copy input files
sh.copyfile(file_mean_epi_source, os.path.join(path_epi_source,"epi.nii"))
sh.copyfile(file_mean_epi_target, os.path.join(path_epi_target,"epi.nii"))
sh.copyfile(file_t1, os.path.join(path_t1,"T1.nii"))
sh.copyfile(file_mask, os.path.join(path_t1,"mask.nii"))

"""
bias field correction to epi
"""
path = [path_epi_source, path_epi_target]
for i in range(len(path)):
    n4 = N4BiasFieldCorrection()
    n4.inputs.dimension = 3
    n4.inputs.input_image = os.path.join(path[i],"epi.nii")
    n4.inputs.bias_image = os.path.join(path[i],'n4bias.nii')
    n4.inputs.output_image = os.path.join(path[i],"bepi.nii")
    n4.run()

"""
clean ana
"""
clean_ana(os.path.join(path_t1,"T1.nii"), 1000.0, 4095.0, overwrite=True)

"""
mask t1 and epi
"""
mask_ana(os.path.join(path_t1,"T1.nii"),os.path.join(path_t1,"mask.nii"))
for i in range(len(path)):
    mask_epi(os.path.join(path[i],"bepi.nii"), 
             os.path.join(path_t1,"pT1.nii"), 
             os.path.join(path_t1,"mask.nii"), 
             niter_mask, sigma_mask)

"""
syn
"""
embedded_antsreg(os.path.join(path_epi_target,"bepi.nii"), # source image
                 os.path.join(path_epi_source,"bepi.nii"), # target image 
                 run_rigid, # whether or not to run a rigid registration first 
                 rigid_iterations, # number of iterations in the rigid step
                 run_affine, # whether or not to run an affine registration first
                 affine_iterations, # number of iterations in the affine step
                 run_syn, # whether or not to run a SyN registration
                 coarse_iterations, # number of iterations at the coarse level
                 medium_iterations, # number of iterations at the medium level
                 fine_iterations, # number of iterations at the fine level
                 cost_function, # CrossCorrelation or MutualInformation
                 interpolation, # interpolation for registration result (NeareastNeighbor or Linear)
                 convergence = 1e-6, # threshold for convergence (can make algorithm very slow)
                 ignore_affine = False, # ignore the affine matrix information extracted from the image header 
                 ignore_header = False, # ignore the orientation information and affine matrix information extracted from the image header
                 save_data = True, # save output data to file
                 overwrite = True, # overwrite existing results 
                 output_dir = path_syn, # output directory
                 file_name = "syn", # output basename
                 )

# rename final deformations
os.rename(os.path.join(path_syn,"syn_ants-map.nii.gz"),
          os.path.join(path_output,"target2source.nii.gz"))
os.rename(os.path.join(path_syn,"syn_ants-invmap.nii.gz"),
          os.path.join(path_output,"source2target.nii.gz"))

"""
apply deformation
"""
# orig -> epi
apply_coordinate_mappings(file_mean_epi_source, # input 
                          os.path.join(path_output,"source2target.nii.gz"), # cmap
                          interpolation = "linear", # nearest or linear
                          padding = "zero", # closest, zero or max
                          save_data = True, # save output data to file (boolean)
                          overwrite = True, # overwrite existing results (boolean)
                          output_dir = path_output, # output directory
                          file_name = "source2target_example" # base name with file extension for output
                          )

# epi -> orig
apply_coordinate_mappings(file_mean_epi_target, # input 
                          os.path.join(path_output,"target2source.nii.gz"), # cmap
                          interpolation = "linear", # nearest or linear
                          padding = "zero", # closest, zero or max
                          save_data = True, # save output data to file (boolean)
                          overwrite = True, # overwrite existing results (boolean)
                          output_dir = path_output, # output directory
                          file_name = "target2source_example" # base name with file extension for output
                          )

# rename final deformation examples
os.rename(os.path.join(path_output,"source2target_example_def-img.nii.gz"),
          os.path.join(path_output,"source2target_example.nii.gz"))
os.rename(os.path.join(path_output,"target2source_example_def-img.nii.gz"),
          os.path.join(path_output,"target2source_example.nii.gz"))

# clean intermediate files
if cleanup:
    sh.rmtree(path_temp, ignore_errors=True)
