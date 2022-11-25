"""
Conversion VMAP -> PERMAS-ASCII of model (no results).

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

from local_imports import sys  # this adds PyVMAP to PATH
import math
import time
import numpy as np
import pandas as pd
from func import VmapRead
from func import auxiliary as aux

# %% startup
# %%% command line arguments
# check command line arguments, and get input file name
INPUTFILENAME, INPUTFILENAME_contituents = aux.check_argv_short(sys.argv, [
                                                                'hdf', 'h5'])

# %%% files and folders
# folders
folder_output = 'data/'
folder_input = 'data/'
# output file name constructed from input file name
OUTPUTFILENAME = '.'.join(
    INPUTFILENAME_contituents[:len(INPUTFILENAME_contituents)-1]) + '_toPERMASASCII.dat'

# check input file's existence
aux.assert_file_exists(folder_input + INPUTFILENAME)

# %% read VMAP
print(aux.sep_big + 'READING VMAP\n' + aux.sep_big)
# determination of process time
times = []
times.append(time.process_time())

parts, points, elements, material, surface, esets, length_esets, nsets = \
    VmapRead.VmapRead(folder_input + INPUTFILENAME, keyword="model")

times.append(time.process_time())
print((aux.sep_small + 'PROCESSTIME FOR READING: {:5.3f}s\n' + aux.sep_small)
      .format(times[-1] - times[-2]))

# %% fill model buffer
print(aux.sep_big + 'FILL MODEL BUFFER\n' + aux.sep_big)

enter_component_string = [
    "$ENTER COMPONENT  NAME = MIXED  DOFTYPE = DISP TEMP"]
situation_string = ["   $SITUATION NAME = MYSITUATION",
                    "      CONSTRAINTS=MYCONSTRAINTS   SYSTEM=MYSYSTEM   LOADING=MYLOADING   RESULTS=MYRESULTS", "   $END SITUATION"]
structure_start_string = ["   $STRUCTURE"]
structure_end_string = ["   $END STRUCTURE"]
constraints_string = [
    "   $CONSTRAINTS NAME = MYCONSTRAINTS", "   $END CONSTRAINTS"]
system_string = ["   $SYSTEM NAME = MYSYSTEM", "   $END SYSTEM"]
loading_string = ["   $LOADING NAME = MYLOADING", "   $END LOADING"]
results_string = ["   $RESULTS NAME = MYRESULTS", "   $END RESULTS"]
exit_component_string = ["$EXIT COMPONENT"]

# model data contains all the strings in correct order which are written into the STRUCTURE part
model_data = []
string_Coor = "      $COOR"
model_data.append(string_Coor)

# print all the coordinates into model_data
points_tostring = points.drop(columns=["part"]).dropna(axis='columns')
# add 10 spaces to the dataframe, for right PERMASASCII convention
empty_string = '          '
points_tostring.insert(0, 'spaces', empty_string)
# format values into string
points_string = points_tostring.to_string(
    index=False, header=False, float_format='%.6e')
model_data.append(points_string)

endstring_Coor = "!"
model_data.append(endstring_Coor)

# %%% elements
# split the elements back to hexe8 and tet10- elements
elements_hexe8 = []
elements_tet10 = []

elements_tet10 = elements[elements.elementtype == 10].drop(
    columns={'part', 'elementtype'})
elements_hexe8 = elements[elements.elementtype == 8].drop(
    columns={'part', 'elementtype'}).dropna(axis='columns')

if len(elements_tet10) != 0:
    string_Tet10 = "      $ELEMENT TYPE = TET10"
    model_data.append(string_Tet10)

    # transfrom dataframe to string
    elements_tet10_tostring = pd.DataFrame(elements_tet10).astype(float)
    # add 10 spaces to the dataframe, for right PERMASASCII convention
    empty_string = '          '
    elements_tet10_tostring.insert(0, 'spaces', empty_string)
    # format values into string
    elements_hexe8_string = elements_tet10_tostring.to_string(
        index=False, header=False, float_format='%.0f')
    model_data.append(elements_hexe8_string)

if len(elements_hexe8) != 0:
    string_Hexe8 = "      $ELEMENT TYPE = HEXE8"
    model_data.append(string_Hexe8)

    # transfrom dataframe to string
    elements_hexe8_tostring = pd.DataFrame(elements_hexe8).astype(float)
    # add 10 spaces to the dataframe, for right PERMASASCII convention
    empty_string = '          '
    elements_hexe8_tostring.insert(0, 'spaces', empty_string)
    # format values into string
    elements_tet10_string = elements_hexe8_tostring.to_string(
        index=False, header=False, float_format='%.0f')
    model_data.append(elements_tet10_string)

# %%% element sets
divider = 14
for i in range(len(parts)):
    # add ESET Name
    eset_string = "      $ESET NAME = %s" % (parts[i][1])
    model_data.append(eset_string)

    # seperate esets from the current part and take only the element numbers
    esets_part = esets[esets.part == parts[i][1]]
    esets_part_np = np.array(esets_part.element)

    # split the nsets in nsets with full rows and the last row
    number_of_full_rows = math.floor(esets_part_np.shape[0]/divider)
    esets_to_resize = esets_part_np[:number_of_full_rows*divider]
    esets_not_to_resize = esets_part_np[number_of_full_rows*divider:]

    if len(esets_to_resize) != 0:
        # FULL ROWS
        # new shape for nsets (here 14 in one row)
        esets_to_resize = np.resize(
            esets_to_resize, (number_of_full_rows, divider))
        # insert spaces only works for pandas Dataframes
        esets_resized_pd = pd.DataFrame(esets_to_resize)
        # add 10 spaces to the dataframe, for right PERMASASCII convention
        empty_string = '          '
        esets_resized_pd.insert(0, 'spaces', empty_string)
        # format values into string
        esets_resized_string = esets_resized_pd.to_string(
            index=False, header=False, float_format='%.0f')
        model_data.append(esets_resized_string)
    if len(esets_not_to_resize) != 0:
        # LAST ROW
        # insert spaces only works for pandas Dataframes
        esets_not_resized_pd = pd.DataFrame([esets_not_to_resize])
        # add 10 spaces to the dataframe, for right PERMASASCII convention
        esets_not_resized_pd.insert(0, 'spaces', empty_string)
        # format values into string
        esets_not_resized_string = esets_not_resized_pd.to_string(
            index=False, header=False, float_format='%.0f')
        model_data.append(esets_not_resized_string)

# %%% nodal sets
if nsets.empty != True:
    name_nsets = sorted(list(set(nsets.NAME)))
    for i in range(len(name_nsets)):
        # add NSET Name
        nset_string = "      $NSET NAME = %s" % (name_nsets[i])
        model_data.append(nset_string)

        # seperate nsets from the current nset and take only the node numbers
        nsets_part = nsets[nsets.NAME == name_nsets[i]]
        nsets_part_np = np.array(nsets_part[0])

        # split the nsets in nsets with full rows and the last row
        number_of_full_rows = math.floor(nsets_part_np.shape[0]/divider)
        nsets_to_resize = nsets_part_np[:number_of_full_rows*divider]
        nsets_not_to_resize = nsets_part_np[number_of_full_rows*divider:]

        if len(nsets_to_resize) != 0:
            # FULL ROWS
            # new shape for nsets (here 14 in one row)
            nsets_to_resize = np.resize(
                nsets_to_resize, (number_of_full_rows, divider))
            # insert spaces only works for pandas Dataframes
            nsets_resized_pd = pd.DataFrame(nsets_to_resize)
            # add 10 spaces to the dataframe, for right PERMASASCII convention
            empty_string = '          '
            nsets_resized_pd.insert(0, 'spaces', empty_string)
            # format values into string
            nsets_resized_string = nsets_resized_pd.to_string(
                index=False, header=False, float_format='%.0f')
            model_data.append(nsets_resized_string)
        if len(nsets_not_to_resize) != 0:
            # LAST ROW
            # insert spaces only works for pandas Dataframes
            nsets_not_resized_pd = pd.DataFrame([nsets_not_to_resize])
            # add 10 spaces to the dataframe, for right PERMASASCII convention
            nsets_not_resized_pd.insert(0, 'spaces', empty_string)
            # format values into string
            nsets_not_resized_string = nsets_not_resized_pd.to_string(
                index=False, header=False, float_format='%.0f')
            model_data.append(nsets_not_resized_string)

# %%% surfaces
if surface.empty != True:
    surface_names = list(surface["NAME"].drop_duplicates())

    for name in surface_names:
        surface_string = "      $SURFACE ELEMENTS  SURFID = %s  SFSET = %s" % \
            (name.split('_')[-1], '_'.join(name.split('_')[:-1]))
        model_data.append(surface_string)

        surface_part = surface[surface['NAME'] == name].drop(columns=["NAME"])\
            .astype('int32')
        # add 10 spaces to the dataframe, for right PERMASASCII convention
        empty_string = '          '
        surface_part.insert(0, 'spaces', empty_string)
        # format values into string
        surface_part_string = surface_part.to_string(
            index=False, header=False, float_format='%.0f')
        model_data.append(surface_part_string)


# %%% material
if material.empty != True:
    material = material.set_axis(list(range(material.shape[1])), axis=1)
    # Material
    material_start_string = ["$ENTER MATERIAL"]
    material_end_string = ["$EXIT MATERIAL"]

    material_string = []
    for i in range(material.shape[1]):
        material_string.extend(["   $MATERIAL  NAME = %s TYPE = ISO" % material.iloc[0][i],
                                "      $ELASTIC  GENERAL  INPUT = DATA",
                                "        %s  %s" % (
                                    material.iloc[1][i], material.iloc[2][i])])
        for j in range(material.shape[0]-3):
            material_string.extend(["      $%s  GENERAL  INPUT = DATA" % material.index[3+j],
                                    "        %s" % material.iloc[3+j][i]])

        material_string.extend(["   $END MATERIAL"])

fin_string = ['$FIN']

times.append(time.process_time())
print((aux.sep_small + 'PROCESSTIME FOR MODEL BUFFER STRINGS: {:5.3f}s\n' + aux.sep_small)
      .format(times[-1] - times[-2]))

# %% write ASCII
print(aux.sep_big + 'WRITE ASCII FILE\n' + aux.sep_big)
# data.post(HyperView) or data.dat(Hypermesh)
with open(folder_output + OUTPUTFILENAME, 'w+') as f:
    # enter component
    for i in range(len(enter_component_string)):
        f.write('%s\n' % enter_component_string[i])
    # start structure
    for i in range(len(structure_start_string)):
        f.write('%s\n' % structure_start_string[i])
    # model data:
    for i in range(len(model_data)):
        f.write('%s\n' % model_data[i])
    # end structure
    for i in range(len(structure_end_string)):
        f.write('%s\n' % structure_end_string[i])
    # Constraints (empty)
    for i in range(len(constraints_string)):
        f.write('%s\n' % constraints_string[i])
    # System (empty)
    for i in range(len(system_string)):
        f.write('%s\n' % system_string[i])
    # Loading (empty)
    for i in range(len(loading_string)):
        f.write('%s\n' % loading_string[i])
    # Results (empty)
    for i in range(len(results_string)):
        f.write('%s\n' % results_string[i])
    # Situation (empty)
    for i in range(len(situation_string)):
        f.write('%s\n' % situation_string[i])
    # exit component
    for i in range(len(exit_component_string)):
        f.write('%s\n' % exit_component_string[i])
    if material.empty == False:
        # start material
        for i in range(len(material_start_string)):
            f.write('%s\n' % material_start_string[i])
        material
        for i in range(len(material_string)):
            f.write('%s\n' % material_string[i])
        # end material
        for i in range(len(material_end_string)):
            f.write('%s\n' % material_end_string[i])
    # fin
    for i in range(len(fin_string)):
        f.write('%s\n' % fin_string[i])

times.append(time.process_time())
print((aux.sep_small + 'PROCESSTIME FOR EVERYTHING: {:5.3f}s\n' + aux.sep_small)
      .format(times[-1] - times[0]))
