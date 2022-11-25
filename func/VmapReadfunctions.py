"""
Helper functions for reading a VMAP file (model and/or results).

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

import pandas as pd
import numpy as np
import PyVMAP as VMAP


def read_geometry_points(file, grp="/VMAP/GEOMETRY/0"):
    """
    Read POINTS of the group /VMAP/GEOMETRY/<PART-ID>.

    Parameters:
    ----------------
    file:   VMAP-file with read access: file=VMAP.VMAPFile(FILENAME,2)
    grp:    VMAP-group or string with path

    Returns:
    --------
    geompandas:     Pandas DataFrame
    """
    geomPointsRead = VMAP.sPointsBlock()
    file.readPointsBlock(grp, geomPointsRead)
    geomIdCo = []
    for i in range(geomPointsRead.mySize):
        # read out coordinates and IDs from the "geomPointsRead" (Points block of the VMAP file)
        geomCoords = [geomPointsRead.myCoordinates[3*i],
                      geomPointsRead.myCoordinates[3*i+1], geomPointsRead.myCoordinates[3*i+2]]
        geomIds = [geomPointsRead.myIdentifiers[i]]

        # geometric Coordinates and geometric IDs in one list
        geom = geomIds.copy()
        geom.extend(geomCoords)
        geomIdCo.append(geom)
    geompandas = pd.DataFrame(geomIdCo, columns=['nodes', 'x', 'y', 'z'])
    return geompandas


def read_geometry_elementtypes(file):
    """
    Read element types and their respective number of nodes from /VMAP/SYSTEM.

    Parameters
    ----------
    file : VMAP-file with read access: file=VMAP.VMAPFile(FILENAME,2)

    Returns
    -------
    elementtypes_dict : dicitonary
        usually {1: 8, 2: 10} (HEXE8 and TET10, respectively)    

    """
    # read out elementtypes
    geomElemTypeRead = VMAP.VectorTemplateElementType()
    file.readElementTypes(geomElemTypeRead)
    # initialize list with zeros that the data can be stacked
    elementypes_list = np.zeros(2)
    for item in geomElemTypeRead:
        # read out the information of the elementtypes in hdf and append Identifier and Nodenumber
        numItem = np.array(
            (item.myIdentifier, item.myNumberOfNodes), dtype=VMAP.sElementType)
        elementypes_list = np.vstack([elementypes_list, numItem])
    # delete the first row with zeros
    elementypes_list = np.delete(elementypes_list, 0, 0)

    elementtypes_dict = dict(elementypes_list)
    for numnodes in elementtypes_dict.values():
        if numnodes != 8 and numnodes != 10:
            print('WARNING: code is only tested for HEX8 and TET10')
    return elementtypes_dict


def read_geometry_elems(file, elementtypes, grp="/VMAP/GEOMETRY/0"):
    """
    Read ELEMENTS of the group /VMAP/GEOMETRY/<PART-ID>.

    Parameters
    ----------
    file:           VMAp-file with read access: file=VMAP.VMAPFile(FILENAME,2)
    elementtypes:   dict with elementtypes and number of nodes per element
    grp:            VMAP-group or string with path

    Returns
    -------
    elemspandas:    Pandas DataFrame
    """
    geomElemsBlockRead = VMAP.sElementBlock()
    file.readElementsBlock(grp, geomElemsBlockRead)
    for i in range(geomElemsBlockRead.myElementsSize):
        geomElementrow = geomElemsBlockRead.getElement(i)
        identifier = [geomElementrow.myIdentifier]
        elementtype = geomElementrow.myElementType

        # read out the number of nodes depending on elementtype from dict
        numnodes = elementtypes[elementtype]
        connectivity = []
        # read out the elements
        for j in range(numnodes):
            connectivity.append(geomElementrow.myConnectivity[j])
        # TET10 elements has to be rearranged, because VMAP has another sequence than PERMAS
        if numnodes == 10:
            connectivity = rearrange_tet10(connectivity)
        elements = identifier.copy()
        elements.extend([numnodes])
        elements.extend(connectivity)
        if i == 0:
            geomelements = []
            geomelements.append(elements)
        else:
            geomelements.append(elements)

    elemspandas = pd.DataFrame(geomelements)
    return elemspandas


def rearrange_tet10(elem_vmap):
    """
    Rearrange TET10 definition, from VMAP to PERMAS.

    Structure:
        VMAP     : PERMAS
        1        : 1
        2        : 3
        3        : 5
        4        : 10
        5        : 2
        6        : 4
        7        : 6
        8        : 7
        9        : 8
        10       : 9

    Parameters:
    ----------------
    elem_vmap: VMAP tet10 element, list containing nodal indices

    Returns:
    --------
    elem_permas: PERMAS tet10 element, list containing nodal indices
    """
    elem_permas = [0]*10
    elem_permas[0] = elem_vmap[0]
    elem_permas[1] = elem_vmap[4]
    elem_permas[2] = elem_vmap[1]
    elem_permas[3] = elem_vmap[5]
    elem_permas[4] = elem_vmap[2]
    elem_permas[5] = elem_vmap[6]
    elem_permas[6] = elem_vmap[7]
    elem_permas[7] = elem_vmap[8]
    elem_permas[8] = elem_vmap[9]
    elem_permas[9] = elem_vmap[3]
    return elem_permas


def rearrange_tet10_res(values):
    """
    Rearrange TET10 data definition, from VMAP to PERMAS.

    Structure:
        VMAP     : PERMAS
        1        : 1
        2        : 3
        3        : 5
        4        : 10
        5        : 2
        6        : 4
        7        : 6
        8        : 7
        9        : 8
        10       : 9

    Parameters:
    ----------------
    values: list
        TET10 data (60 values) in VMAP order

    Returns:
    --------
    elements: Pandas Dataframe
    """
    elems = []
    for i in range(6*6):
        elems.insert(0, values.pop())
    for i in range(6):
        elems.insert(6*6, values.pop())
    for i in range(6):
        elems.insert(6*2, values.pop())
    for i in range(6):
        elems.insert(6*1, values.pop())
    for i in range(6):
        elems.insert(6*0, values.pop())
    return elems


def read_variables_points(file, index, grp="/VMAP/VARIABLES/STATE-0/0/", state="0", variablestype="DISPLACEMENT"):
    """
    Read VARIABLES with respect to POINTS.

    Parameters
    ----------
    file:   VMAP-file with read access: file=VMAP.VMAPFile(FILENAME,2)
    index:  Pandas DataFrame
        points from VMAP Geometry (what the variables are dependend on)
    grp:    VMAP-group or string with path
    state:  state time
    variablestype: name of variable type (string)

    Returns
    -------
    variablespandas:    Pandas DataFrame
    """
    VariablesRead = VMAP.sStateVariable()
    file.readVariable(grp+variablestype, VariablesRead)
    Ids = VariablesRead.getGeometryIds()

    # if geometry ids exist, the variable is not defined for every node
    if len(Ids) > 0:
        counter = len(Ids)
    else:
        counter = index.shape[0]
    variables = []
    # count over all variables of this variabletype
    for i in range(counter):
        dimension = VariablesRead.myDimension
        multiplicity = VariablesRead.myMultiplicity
        values = []
        for j in range(dimension*multiplicity):
            values.append(
                VariablesRead.myValues[j+i*dimension*multiplicity])
        # Element stress with Tet10:
        if len(values) == 60:
            values = rearrange_tet10_res(values)

        variables.append(values)

    variablespandas = pd.DataFrame(variables)
    if len(Ids) > 0:
        variablespandas.insert(0, 'index', Ids)
    else:
        variablespandas.insert(0, 'index', index[:])
    variablespandas.insert(1, 'State', state)
    variablespandas.insert(2, 'Variabletype', variablestype)

    return variablespandas


def read_materialdata(file):
    """
    Read MATERIALS.

    Parameters
    ----------
    file:   VMAP-file with read access: file=VMAP.VMAPFile(FILENAME,2)

    Returns
    -------
    material_complete : Pandas DataFrame
    """
    MaterialReadVector = VMAP.VectorTemplateMaterial()
    file.readMaterialBlock(MaterialReadVector)

    material_complete = pd.DataFrame([])
    for item in MaterialReadVector:
        material_data = []
        material = np.array((item.myIdentifier, item.myMaterialDescription, item.myMaterialName,
                             item.myMaterialState, item.myMaterialSupplier, item.myMaterialType,
                             ), dtype=VMAP.sMaterial)
        material_data.append(['NAME', material[2]])
        material_parameters_vec = []
        for i in range(len(item.myMaterialCard.myParameters)):
            material_parameters = np.array((item.myMaterialCard.myParameters[i].myName,
                                            item.myMaterialCard.myParameters[i].myDescription,
                                            item.myMaterialCard.myParameters[i].myValue), dtype=VMAP.sParameter)
            material_parameters_vec.append(material_parameters)

        for j in range(len(material_parameters_vec)):
            name = material_parameters_vec[j][0]
            value = material_parameters_vec[j][2]
            material_data.append([name, value])
        material_pd = pd.DataFrame(material_data).set_index(0)
        material_complete = pd.concat([material_complete, material_pd], axis=1)

    return material_complete
