"""
Function reading a VMAP file (model and/or results).

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

import numpy as np
import pandas as pd
import PyVMAP as VMAP
from func import VmapReadfunctions as readfunc


def VmapRead(FILENAME, keyword="both"):
    """
    Read model and/or result data from VMAP and return Pandas DataFrames.

    TODO: update documentation of outputs

    Input: 
    -------------------
    FILENAME: Input-Filename of the Vmap-File
    keyword: decide which data should be read out from VMAP
             Options: - model: read out only model data to save model data as ascii
                      - results: read out only results to save as hwascii
                      - both: default value, read out model and results

    Output: [not up to date!]
    -------------------
    parts:          list, optional
        ID's and names of parts.
    points:         Pandas DataFrame
        Nodal ID's and coordinates.
    stresses:       Pandas DataFrame
        Nodal stresses.
    elements:       Pandas DataFrame, optional
        Element definitions.
    elems_res:      Pandas DataFrame, optional
        Element results, WARNING: untested.
    material:       Pandas DataFrame, optional
    surface:        Pandas DataFrame, optional
        Surface data for $SURFACE and $SFSET.
    esets:          Pandas DataFrame, optional
        Element sets.
    length_esets:   list, optional
        Number of elements per eset.
    nsets:          Pandas Data Frame

    """
    file = VMAP.VMAPFile(FILENAME, 2)

    material = readfunc.read_materialdata(file)

    # GEOMETRY Definition
    geometry = "/VMAP/GEOMETRY/"
    # read out the part-numbers automatically
    geom_list = file.getSubGroups(geometry)

    # read out the partnames (Attribute MYNAME)
    parts = []
    for i in range(len(geom_list)):
        name = file.getStringAttribute(geometry+'%s' % (geom_list[i]), 'MYNAME')
        parts.append([i, name])

    # VARIABLES Definition
    variables = "/VMAP/VARIABLES/"
    states = file.getSubGroups(variables)

    # define empty Datasets
    points = pd.DataFrame([])
    nsets = pd.DataFrame([])
    surface = pd.DataFrame([])
    elements = pd.DataFrame([])
    variable = pd.DataFrame([])
    elems_res = pd.DataFrame([])

    # %% POINTS
    # GEOMETRY NODES - required for every keyword
    for i in range(len(parts)):
        # read out the geom points for every part
        points_part = readfunc.read_geometry_points(
            file, grp=geometry+'%s' % (parts[i][0]))
        # add column "part"
        points_part.insert(1, 'part', parts[i][1])
        # append to complete dataframe
        points = points.append(points_part)
    points = points.drop_duplicates()

    # %% GEOMETRYSETS
    # NSET and SURFACE - only required for model
    if keyword != "results":
        for part in parts:
            geometrysetVector = VMAP.VectorTemplateGeometrySet()
            file.readGeometrySets(
                '/VMAP/GEOMETRY/'+str(part[0]), geometrysetVector)
            for myset in geometrysetVector:
                if myset.getSetType() == 0:  # nodal set
                    if myset.getSetIndexType() == 1:  # single value per node
                        myset_pd = pd.DataFrame(myset.getGeometrySetData())
                        myset_pd['NAME'] = myset.getSetName()
                        nsets = nsets.append(myset_pd)
                    else:
                        print(
                            "ERROR: nodal set with multiple values is not implemented")
                elif myset.getSetType() == 1:  # elemental set
                    if myset.getSetIndexType() == 2:  # pair of values per element
                        myset_pd_temp = pd.DataFrame(myset.getGeometrySetData())
                        myset_pd = pd.DataFrame(np.concatenate(
                            (np.array(myset_pd_temp[::2]), np.array(myset_pd_temp[1::2])), axis=1))
                        myset_pd['NAME'] = myset.getSetName()
                        surface = surface.append(myset_pd)
                    else:
                        print(
                            "ERROR: elemental set with single value is not implemented")
                else:
                    print("ERROR: you have violated the VMAP standard")

    # %% ELEMENTS
    # get a dict of elementtypes and size of elements (HEXE8 = 8, TET10 = 10))
    elementtypes = readfunc.read_geometry_elementtypes(file)

    length_esets = []
    for i in range(len(parts)):
        elements_parts = readfunc.read_geometry_elems(
            file, elementtypes, grp=geometry+'%s' % (parts[i][0]))
        elements_parts.insert(1, 'part', parts[i][1])

        elements = elements.append(elements_parts)
        # safe the length of individual elements for esets
        length_esets.append(len(elements_parts))
    elements.rename(columns={0: 'element', 1: 'elementtype'}, inplace=True)
    esets = elements.set_index(np.arange(elements.shape[0]))
    elements = elements.sort_values(by=['element'])
    elements = elements.drop_duplicates()
    esets = esets.drop_duplicates()

    # %% VARIABLES
    if keyword != "model" and len(states) != 0:
        # read out every State-n
        for n in range(len(states)):
            state_times = file.getVariableStateInformation(n)
            for i in range(len(parts)):
                variablestypes = file.getSubGroups(
                    variables+states[n]+"/%s" % (parts[i][0]))
                # das hier jedes mal auszurechnen braucht ziemlich viel zeit
                points_part = points[points.part == parts[i][1]].nodes
                elements_parts = elements[elements.part == parts[i][1]].element
                for j in range(len(variablestypes)):
                    #-------- VARIABLE ELEMENTS -------------------------------------------------#
                    if "ELEMENT" in variablestypes[j]:
                        elems_res_part = readfunc.read_variables_points(
                            file, elements_parts, grp=variables+states[n]+'/%s/' % (parts[i][0]), state=state_times[1], variablestype=variablestypes[j])
                        elems_res = elems_res.append(elems_res_part)
                    else:
                        #-------- VARIABLE NODES ----------------------------------------------------#
                        variable_part = readfunc.read_variables_points(
                            file, points_part, grp=variables+states[n]+'/%s/' % parts[i][0], state=state_times[1], variablestype=variablestypes[j])
                        variable = variable.append(variable_part)

        # drop duplicate rows
        elems_res = elems_res.drop_duplicates()
        variable = variable.drop_duplicates()

    file.closeFile()

    if keyword == "model":
        return parts, points, elements, material, surface, esets, length_esets, nsets
    elif keyword == "results":
        return points, elems_res, variable
    else:
        return parts, points, elements, material, surface, esets, length_esets, nsets, elems_res, variable
