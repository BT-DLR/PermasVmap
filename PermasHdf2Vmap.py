"""
Conversion from Permas-HDF to VMAP of model (and optional results).

Usage, requirements: see README.md
Paradigm, code style: see CONTRIBUTING.md

Copyright 2022 German Aerospace Center (DLR e.V.)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import h5py
import numpy as np
import time
import progressbar
import math
from local_imports import sys  # this adds PyVMAP to PATH
import PyVMAP as VMAP
from func import VmapWrite, PermasModelRead, PermasModelPostprocess, PermasResultsRead
from func import auxiliary as aux

# %% startup
# %%% command line arguments
# check command line arguments, and get input file names
# all but the first 2 return values are optional
INPUTFILENAME_model, \
    INPUTFILENAME_model_contituents, \
    INPUTFILENAME_results, \
    INPUTFILENAME_results_contituents, \
    timesteps_user, \
    variables_node_user = aux.check_argv(sys.argv, ['hdf', 'h5'])

# %%% files and folders
# folder for input and output data
folder_data = './data/'

# output file name constructed from input file name
OUTPUTFILENAME = '.'.join(
    INPUTFILENAME_model_contituents[:len(INPUTFILENAME_model_contituents)-1]) + '_toVMAP.hdf'

# check input file's existence
aux.assert_file_exists(folder_data + INPUTFILENAME_model)

# load the model input file
inputfile_model = h5py.File(folder_data + INPUTFILENAME_model, 'r')
# if no file for results is defined, use the model input file
if INPUTFILENAME_results != '':
    aux.assert_file_exists(folder_data + INPUTFILENAME_results)
    inputfile_results = h5py.File(folder_data + INPUTFILENAME_results, 'r')
else:
    inputfile_results = inputfile_model
    INPUTFILENAME_results = INPUTFILENAME_model

print('input file for model:   ' + INPUTFILENAME_model +
      '\ninput file for results: ' + INPUTFILENAME_results + '\n')

# %%% helper variables
# variables of nodes and elements, which can be read out
variable_nodes_exist = ['DISPLACEMENT', 'CONTACT STATUS', 'NODAL POINT STRAIN',
                        'NODAL POINT STRESS', 'GAP WIDTH', 'TEMPERATURE']
variable_elem_exist = ['ELEMENT STRESS', 'ELEMENT STRAIN']

timesteps_user, variables_node_user = aux.determine_times_vars(
    timesteps_user, variables_node_user, variable_nodes_exist)

# %% read PERMAS
print(aux.sep_big + 'READING PERMAS\n' + aux.sep_big)
# determination of process time
times = []
times.append(time.process_time())
# %%% GEOMETRY
# read
nodes, \
    esets, \
    partnames, \
    elements_hexe8, \
    elements_tet10, \
    sfsets_names, \
    sfsets_ids, \
    surfs_ids, \
    surfs, \
    surfs_flat, \
    nsets, \
    nsets_names, \
    materials, \
    eset_material, \
    coorsystems \
    = PermasModelRead.PermasModelRead(inputfile_model)

# some post-processing
nodes, \
    esets, \
    partnames, \
    elements_hexe8, \
    elements_tet10, \
    nodes_all_ids, \
    esets_types, \
    elements_hexe8_ids, \
    elements_tet10_ids, \
    nsets_first, \
    surfs_firstel \
    = PermasModelPostprocess.PermasModelPostprocess(
        nodes,
        esets,
        partnames,
        elements_hexe8,
        elements_tet10,
        surfs_ids,
        surfs,
        nsets)

times.append(time.process_time())
print((aux.sep_small + 'PROCESSTIME FOR READING AND POSTPROCESSING MODEL: {:5.3f}s\n' + aux.sep_small)
      .format(times[-1] - times[-2]))

# %%% VARIABLES
timesteps_list, \
    variablestypes_nodes_list, \
    node_results_pd \
    = PermasResultsRead.PermasResultsRead(
        inputfile_results,
        timesteps_user,
        variables_node_user)
print('timesteps:', timesteps_list)
print()

times.append(time.process_time())
print((aux.sep_small + 'PROCESSTIME FOR READING RESULTS: {:5.3f}s\n' + aux.sep_small)
      .format(times[-1] - times[-2]))


# %% write VMAP
print(aux.sep_big + 'WRITING VMAP\n' + aux.sep_big)
outputfile = VMAP.VMAPFile(folder_data + OUTPUTFILENAME)

# define element types
esettype_to_vmapelemtype = {'HEXE8': 1, 'TET10': 2}

VmapWrite.VmapWriteInitial(outputfile)

# %%% MATERIAL
# create and fill the MATERIAL group bottom-up: PARAMETERS -> MATERIALCARD -> <MAT> -> MATERIAL
print('writing MATERIAL ... ', end='')
VmapWrite.VmapWriteMaterial(outputfile, materials)
print('done')
print()

# %%% SYSTEM
print('writing SYSTEM ...')
# %%%% ELEMENTTYPES
VmapWrite.VmapWriteEtypeItype(outputfile, esets_types, esettype_to_vmapelemtype)

# %%%% COORDINATESYSTEMS
VmapWrite.VmapWriteCoorsys(outputfile, coorsystems)
print()

# %%% GEOMETRY
print('writing GEOMETRY ...')
times.append(time.process_time())
parts_numnodes, esets_nodes_unique = \
    VmapWrite.VmapWriteGeometry(outputfile,
                                partnames,
                                nodes,
                                nodes_all_ids,
                                nsets_names,
                                esets,
                                esets_types,
                                eset_material,
                                esettype_to_vmapelemtype,
                                elements_hexe8,
                                elements_hexe8_ids,
                                elements_tet10,
                                elements_tet10_ids,
                                nsets,
                                nsets_first,
                                surfs_ids,
                                surfs_firstel,
                                surfs_flat,
                                sfsets_ids,
                                sfsets_names,
                                materials)

times.append(time.process_time())
print((aux.sep_small + 'PROCESSTIME FOR WRITING GEOMETRY: {:5.3f}s\n' + aux.sep_small)
      .format(times[-1] - times[-2]))

# %%% VARIABLES
num_noderesults = len(node_results_pd)
if num_noderesults > 0:
    print('writing VARIABLES ...')
    # %%%% assign POINTS to PARTS
    # TODO this is the bottleneck of the overall performance. to improve, one might
    # have to get rid of pandas
    print('assigning nodes to parts ... ', flush=True)
    # because this may take long, let's have a progressbar
    widget = [' [',
              progressbar.Timer(format='elapsed time: %(elapsed)s'),
              '] ',
              progressbar.Bar('*'), ' (',
              progressbar.ETA(), ') ',
              ]
    # to keep the slowdown due to progressbar minimal, we only want to resolve progress with 0.1 to 1.0% accuracy
    # on the dev's machine and with the provided test data, this still slows the overall process down from ~5.5s to ~5.8s
    if num_noderesults < 100:
        print('ERROR: progressbar requires at least 100 nodal results')
        sys.exit(1)
    num_noderesults_order = int(math.log10(num_noderesults))
    divisor = 10**(num_noderesults_order - 2)
    bar_max_value = int(num_noderesults/divisor)
    bar = progressbar.ProgressBar(
        max_value=bar_max_value, widgets=widget).start()
    ct_bar = 0
    # go
    if timesteps_list != [] and variablestypes_nodes_list != []:
        nodes_results_part_list = [None]*len(node_results_pd)
        node_results_pd = node_results_pd.rename(columns={'Index': 'EID'})
        node_results_pd = node_results_pd.set_index(
            np.arange(node_results_pd.shape[0]))
        for i in range(len(node_results_pd)):
            if i % divisor == 0:
                bar.update(ct_bar)
                ct_bar += 1
            node = node_results_pd.node[i]
            # find part of current node
            found_part_of_node = False
            for ct_part, partname in enumerate(partnames):
                if node in esets_nodes_unique[ct_part]:
                    nodes_results_part_list[i] = partname
                    found_part_of_node = True
                    break
            if not found_part_of_node:
                print('ERROR: could not find part of node')
                sys.exit(1)
        node_results_pd = node_results_pd.assign(PART=nodes_results_part_list)
    times.append(time.process_time())
    # print('done [took {:5.3f}s]'.format(times[-1] - times[-2])) # don't print this when there's a progressbar
    print()

    # %%%% timesteps
    print('setting timesteps ... ', end='')
    for i in range(len(timesteps_list)):
        outputfile.setVariableStateInformation(
            i, 'timestep_%s' % i, timesteps_list[i], timesteps_list[i], -1)
    print('done')

    # %%%% groups
    print('creating groups ... ', end='')
    variables_groups = []
    for j in range(len(timesteps_list)):
        var_group_timestep = []
        for i in range(len(partnames)):
            variables_part = outputfile.createVariablesGroup(j, i)
            var_group_timestep.append(variables_part)
        variables_groups.append(var_group_timestep)
    print('done')

    # %%%% nodal
    times.append(time.process_time())
    print('writing results ...')
    if node_results_pd.empty == False:
        for n in range(len(timesteps_list)):
            print('  time: ' + str(timesteps_list[n]))
            node_results_timestep_pd = node_results_pd[node_results_pd.timestep ==
                                                       timesteps_list[n]].drop(columns=['timestep'])
            for i in range(len(partnames)):
                print('    part: ' + partnames[i])
                nodes_results_part_pd = node_results_timestep_pd[node_results_timestep_pd.PART == partnames[i]].drop(columns=[
                    'PART'])
                for j in range(len(variablestypes_nodes_list)):
                    print('      variable: ' + variablestypes_nodes_list[j])
                    node_results_vartype_pd = nodes_results_part_pd[nodes_results_part_pd.variabletype == variablestypes_nodes_list[j]].drop(columns=[
                        'variabletype'])
                    if node_results_vartype_pd.empty:
                        continue
                    node_results_vartype_pd = node_results_vartype_pd.dropna(
                        axis='columns')
                    VmapWrite.VmapWriteVariables(outputfile,
                                                 node_results_vartype_pd,
                                                 result_type=variablestypes_nodes_list[j],
                                                 state=timesteps_list[n],
                                                 part_id=i,
                                                 part_length=parts_numnodes[partnames[i]],
                                                 dimension=node_results_vartype_pd.shape[1]-1,
                                                 incrementvalue=j,
                                                 location=2,
                                                 description=variablestypes_nodes_list[j] +
                                                 partnames[i],
                                                 grp=variables_groups[n][i])
    print('done [took {:5.3f}s]'.format(times[-1] - times[-2]))
else:
    print('no VARIABLES')

# %% finish
inputfile_model.close()
inputfile_results.close()
outputfile.closeFile()

times.append(time.process_time())
print((aux.sep_small + 'PROCESSTIME FOR EVERYTHING: {:5.3f}s\n' + aux.sep_small)
      .format(times[-1] - times[0]))
