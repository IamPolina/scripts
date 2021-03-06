"""
Sample volume data on surface

The purpose of the following script is to sample data to a surface in native epi space and map those
data to the surface in conformed freesurfer space.

created by Daniel Haenelt
Date created: 07-02-2019
Last modified: 13-01-2020
"""
import os
from lib.mapping.map2surface import map2surface

# input files
path_input = "/data/pt_01880/Experiment1_ODC/p3/deformation/odc/GE_EPI1_rigid/epi_surf"
path_output = "/data/pt_01880/Experiment1_ODC/p3/odc/results/spmT/surf"
input_vol = "/data/pt_01880/Experiment1_ODC/p3/odc/results/spmT/native/spmT_left_right_GE_EPI1.nii"
input_white = "/data/pt_01880/Experiment1_ODC/p3/anatomy/layer/lh.layer10"
n_layer = 11
cleanup = True

""" do not edit below """

hemi = ["lh","rh"]
for i in range(n_layer):
    for j in range(len(hemi)):

        # get input filenames in the input path        
        input_surf = os.path.join(path_input,hemi[j]+".layer"+str(i)+"_def")
        input_ind = os.path.join(path_input,hemi[j]+".layer"+str(i)+"_ind.txt")
 
        # deform surface
        map2surface(input_surf, input_vol, hemi[j], path_output, input_white, input_ind, cleanup)