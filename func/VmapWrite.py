"""
Functions for writing the VMAP file.

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

import PyVMAP as VMAP
import numpy as np
import datetime
import sys


def VmapWriteInitial(openfile):
    """
    Initialize VMAP file.

    Parameters
    ----------
    openfile : open VMAPFile

    Returns
    -------
    None.

    """
    VMAP.Initialize()
    # set version attribute automatically from __PyVMAP
    VMAP.sVersion()

    # set metadata
    hour = datetime.datetime.now().hour
    minute = datetime.datetime.now().minute
    second = datetime.datetime.now().second
    time = '%s:%s:%s' % (hour, minute, second)
    metaInfo = VMAP.sMetaInformation()
    metaInfo.setExporterName('Permashdf2Vmap')
    metaInfo.setFileDate(str(datetime.date.today()))
    metaInfo.setFileTime(time)
    # metaInfo.setDescription('Description')
    # metaInfo.setAnalysisType('AnalysisType')
    # metaInfo.setUserId('UserID')

    openfile.writeMetaInformation(metaInfo)

    # set unit information
    myUnitSystem = VMAP.sUnitSystem()

    myUnitSystem.getLengthUnit().setUnitSymbol('mm')
    myUnitSystem.getLengthUnit().setSIScale(0.001)
    myUnitSystem.getMassUnit().setUnitSymbol('t')
    myUnitSystem.getMassUnit().setSIScale(1000)
    myUnitSystem.getTimeUnit().setUnitSymbol('s')
    myUnitSystem.getCurrentUnit().setUnitSymbol('A')
    myUnitSystem.getTemperatureUnit().setUnitSymbol('K')
    myUnitSystem.getAmountOfSubstanceUnit().setUnitSymbol('mol')
    myUnitSystem.getLuminousIntensityUnit().setUnitSymbol('cd')
    openfile.writeUnitSystem(myUnitSystem)

    systems = []
    systems.append(
        np.array((8, 'N', (1, 1, -2, 0, 0, 0, 0)), dtype=VMAP.sUnit))
    systems.append(
        np.array((9, 'mm^2', (2, 0, 0, 0, 0, 0, 0)), dtype=VMAP.sUnit))
    systems.append(
        np.array((10, 'MPa', (-1, 1, -2, 0, 0, 0, 0)), dtype=VMAP.sUnit))
    systems.append(
        np.array((11, 'mJ', (2, 1, -2, 0, 0, 0, 0)), dtype=VMAP.sUnit))
    systems.append(
        np.array((12, 'mW', (2, 1, -3, 0, 0, 0, 0)), dtype=VMAP.sUnit))

    unitSystem = VMAP.VectorTemplateUnit()

    for item in systems:
        myUnit = VMAP.sUnit()
        myUnit.setIdentifier(item[0])
        myUnit.setUnitSymbol(item[1])
        myUnit.setUnitDimension(item[2])
        unitSystem.push_back(myUnit)
    openfile.writeUnits(unitSystem)

    return


def VmapWriteVariables(openfile,
                       results,
                       result_type="Displacement",
                       state="STATE-0",
                       part_id=0,
                       part_length=0,
                       coordinatesystem=1,
                       dimension=1,
                       entity=1,
                       identifier=-1,
                       incrementvalue=-1,
                       location=1,
                       multiplicity=1,
                       timevalue=-1,
                       unit=-1,
                       description='description not defined',
                       grp=None):
    """
    Write variables to VMAP.

    Parameters
    ----------
    openfile : open VMAPfile
    results : Pandas dataframe
    all other parameters: self-explanatory

    Returns
    -------
    None.

    """
    if grp == None:
        grp = "/VMAP/VARIABLES/%s/%s/" % (state, part_id)
    variable = VMAP.sStateVariable()

    results = np.array(results)

    # Coordinatesystem kartesian = 1, cylindircal = 2,3
    variable.setCoordinateSystem(coordinatesystem)
    # my dimension = number of columns
    variable.setDimension(dimension)
    # my entity = 1 for real, 2 for complex, 3 for hamiltonian
    variable.setEntity(entity)
    # my Identifier = unique identifier for the variable type (Displacement,..)
    variable.setIdentifier(identifier)
    # my incrementvalue = step value for the stats variable
    variable.setIncrementValue(incrementvalue)
    # set Location (1 = Global, 2 = Nodes, 3 = Elements) where the variable is stored
    variable.setLocation(location)
    # set Multiplicity and Dimension to define the Columns (Muliplicity*Dimension)
    variable.setMultiplicity(multiplicity)
    # set mytimevalue = time of PERMAS Calculation
    variable.setTimeValue(timevalue)
    # set my Unit -> like in unitsystem
    variable.setUnit(unit)
    # set variable describtion
    variable.setVariableDescription(description)
    # set name = Displacement, Stress,...
    variable.setVariableName('%s' % result_type)

    # if location at integration point, set integrationtypes
    if location == 4:
        IntegrationType = int(dimension/6)

    # geometric IDs are optional - only used if state variable is defined over a set
    if part_length != results.shape[0]:
        geomIDs = results[:, 0]
        geomIDs = geomIDs.astype(int)

    results_without_index = np.delete(results, 0, 1)

    results_to_file = results_without_index.reshape(
        results_without_index.shape[0]*results_without_index.shape[1])

    # geometric IDs are optional - only used when state variable is defined over a set
    if part_length != results.shape[0]:
        variable.setGeometryIds(geomIDs.tolist())

    variable.setValues(results_to_file.tolist())
    openfile.writeVariable(grp, variable)
    return


def VmapWriteCoorsys(outputfile, coorsystems):
    """
    Write coordinate systems to VMAP.

    ATTENTION: this is not yet correct, see TODO in the code.

    Parameters
    ----------
    outputfile : open VMAPFile
    coorsystems : see PermasModelRead

    Returns
    -------
    None.

    """
    coordinateVector = VMAP.VectorTemplateCoordinateSystem()

    # write system to testVector
    for csys in coorsystems:
        print('  defining COORDINATESYSTEM (' + str(int(csys[0])) + ')')
        csysVMAP = VMAP.sCoordinateSystem()
        csysVMAP.myIdentifier = int(csys[0])
        csysVMAP.myType = VMAP.sCoordinateSystem.NON_ORTHOGONAL
        csysVMAP.setReferencePoint((csys[1], csys[2], csys[3]))
        # TODO implement transformation from PERMAS RZ form to VMAP
        csysVMAP.setAxisVector(0, csys[4:7])
        csysVMAP.setAxisVector(1, csys[7:10])
        # csysVMAP.setAxisVector(2, item[3][6:9])
        coordinateVector.push_back(csysVMAP)

    outputfile.writeCoordinateSystems('/VMAP/SYSTEM', coordinateVector)
    return


def VmapWriteEtypeItype(outputfile, esets_types, esettype_to_vmapelemtype):
    """
    Write element types and integration types to VMAP.

    Parameters
    ----------
    outputfile : open VMAPFile
    esets_types : see PermasModelPostprocess
    esettype_to_vmapelemtype : dictionary
        Maps Permas element type names to VMAP element type numbers.

    Returns
    -------
    None.

    """
    elementTypeVector = VMAP.VectorTemplateElementType()
    integrationTypeVector = VMAP.VectorTemplateIntegrationType()
    processed_eset_types = []
    for eset_type in esets_types:
        if not eset_type in processed_eset_types:  # check if this type of element has already been processed
            processed_eset_types.append(eset_type)
            if eset_type == 'HEXE8':
                print('  defining VMAP_HEXAHEDRON_8 element and its integration type')
                myIntegrationType = VMAP.VMAPIntegrationTypeFactory.createVMAPIntegrationType(
                    VMAP.VMAPIntegrationTypeFactory.GAUSS_HEXAHEDRON_8)
                HEXE8_ElementType = VMAP.VMAPElementTypeFactory.createVMAPElementType(
                    VMAP.sElementType.ELEM_3D,
                    VMAP.sElementType.HEXAHEDRON_8,
                    VMAP.sElementType.TRILINEAR,
                    myIntegrationType.getIdentifier())
                HEXE8_ElementType.setIdentifier(
                    esettype_to_vmapelemtype['HEXE8'])
                elementTypeVector.push_back(HEXE8_ElementType)
                integrationTypeVector.push_back(myIntegrationType)
            if eset_type == 'TET10':
                print('  defining VMAP_TETRAHEDRON_10 element and its integration type')
                myIntegrationType = VMAP.VMAPIntegrationTypeFactory.createVMAPIntegrationType(
                    VMAP.VMAPIntegrationTypeFactory.GAUSS_TETRAHEDRON_4)  # TODO check
                TET10_ElementType = VMAP.VMAPElementTypeFactory.createVMAPElementType(
                    VMAP.sElementType.ELEM_3D,
                    VMAP.sElementType.TETRAHEDRON_10,
                    VMAP.sElementType.TRIQUADRATIC,
                    myIntegrationType.getIdentifier())
                TET10_ElementType.setIdentifier(
                    esettype_to_vmapelemtype['TET10'])
                integrationTypeVector.push_back(myIntegrationType)
                elementTypeVector.push_back(TET10_ElementType)

    outputfile.writeElementTypes(elementTypeVector)
    outputfile.writeIntegrationTypes(integrationTypeVector)
    return


def VmapWriteMaterial(outputfile, materials):
    """
    Write materials to VMAP.

    Parameters
    ----------
    outputfile : open VMAPFile
    materials : see PermasModelRead

    Returns
    -------
    None.

    """
    materialVector = VMAP.VectorTemplateMaterial()
    for material in materials:
        # PARAMETERS
        material_parameter_vec = []
        for param in material:
            if not param == 'name' and not param == 'id':
                material_parameter = VMAP.sParameter()
                material_parameter.setName(param)
                material_parameter.setDescription('-')
                material_parameter.setValue(str(material[param]))
                material_parameter_vec.append(material_parameter)

        # MATERIALCARD
        # ATM, only solid materials are implemented
        myMaterialCard = VMAP.sMaterialCard()
        myMaterialCard.setIdealization('isotropic')
        myMaterialCard.setIdentifier(material['name'])
        myMaterialCard.setModelName('-')
        myMaterialCard.setPhysics('solid mechanics')
        myMaterialCard.setSolution('-')
        myMaterialCard.setSolver('PERMAS')
        myMaterialCard.setSolverVersion('-')
        myMaterialCard.setUnitSystem('/VMAP/SYSTEM/UNITS(YSTEM)')
        myMaterialCard.setParameters(material_parameter_vec)

        # MAT
        myMaterial = VMAP.sMaterial()
        myMaterial.setMaterialDescription('-')
        myMaterial.setIdentifier(material['id'])
        myMaterial.setMaterialName(material['name'])  # name of <MAT>
        myMaterial.setMaterialState('solid')
        myMaterial.setMaterialSupplier('-')
        myMaterial.setMaterialType('-')
        myMaterial.setMaterialCard(myMaterialCard)
        materialVector.push_back(myMaterial)

    # write
    if materialVector.size() > 0:
        outputfile.writeMaterialBlock(materialVector)
    return


# ATTENTION: this function must be defined last in this file in order for the
# Spyder outline to be correctly displayed. If another function is defined
# below, then the outline might be distorted.
def VmapWriteGeometry(outputfile,
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
                      materials):
    """
    Write GEOMETRY group to VMAP file.

    TODO: reference to coordinate system is not set, see TODO in code below.

    Parameters
    ----------
    outputfile : open VMAPFile
    all other parameters: see PermasModelRead or PermasModelPostprocess

    Returns
    -------
    parts_numnodes : dictionary
        Relates partnames to number of nodes within the respective part.
    esets_nodes_unique : list of np.arrays of int32
        For each part contains an array of unique node indices within that
        part.

    """
    # TODO: standard coordinate system needs to be written to VMAP and be correctly refered to from ELEMENTS. to this end, its ID needs to be determined dynamically because there might be arbitrary other coor sys ID's
    coordinatesystem = -1  # global standard cartesian coor sys.
    geometry_groups = []
    parts_numnodes = {}
    for ct_part, partname in enumerate(partnames):
        geometry_part = outputfile.createGeometryGroup(
            ct_part, partname)
        geometry_groups.append(geometry_part)

    # part-by-part final postprocessing and writing of VMAP
    # by combining postproc and writing in single loop, everything is more on-the-fly and requires less memory
    esets_nodes_unique = []
    for ct_eset, eset in enumerate(esets):  # loop over all parts
        print('processing part ' + partnames[ct_eset])
        part_group = geometry_groups[ct_eset]

        # %%% material ID of part
        mat_id = -1
        found_mat = False
        if len(eset_material) > 0:
            for material in materials:
                if eset_material[partnames[ct_eset]] == material['name']:
                    mat_id = material['id']
                    print('  material: ' +
                          material['name'] + ' (' + str(mat_id) + ')')
                    found_mat = True
                    break
        if not found_mat:
            print('  WARNING: no material found. setting ID=-1, continuing')

        # %%% ELEMENTS & eset_definition
        # this will find the element definitions of eset, i.e. of the current part
        # this is necessary because PERMAS lacks the part-hierarchy. instead, the model definition is always 'flat'
        # paradigm: loop exactly once through global list of element definitions

        # set current elements depending on type of eset. this is efficient because of aliasing.
        if esets_types[ct_eset] == 'HEXE8':
            current_elements = elements_hexe8
            current_elements_ids = elements_hexe8_ids
        elif esets_types[ct_eset] == 'TET10':
            current_elements = elements_tet10
            current_elements_ids = elements_tet10_ids
        else:
            print('ERROR: something wrong with type of eset')
            sys.exit(1)
        # set counters and max counter value
        ct_elem_all = -1
        ct_elem_set = -1
        ct_elem_all_max = current_elements_ids.shape[0]  # just for debugging
        # allocate memory for element definitions
        eset_definition = np.zeros(
            (len(eset), current_elements.shape[1]), dtype=np.int32)
        # loop over elements of eset
        for eid in eset:
            # TODO if there is any other conversion of members of eset, then pre-convert esets in PermasPostprocess
            eid_int = int(eid)
            while True:
                ct_elem_all += 1
                if ct_elem_all == ct_elem_all_max:
                    print('DEBUG ERROR: eid is not part of current_elements_ids')
                    break
                # found element's id
                if current_elements_ids[ct_elem_all] == eid_int:
                    ct_elem_set += 1
                    # store element's definition
                    eset_definition[ct_elem_set, :] = \
                        current_elements[ct_elem_all, :]
                    break
        # create element block, fill it with elements, and write it to VMAP file
        print('  ELEMENTS ... ', end='')
        elemBlock = VMAP.sElementBlock(eset_definition.shape[0])
        # -1 because definition contains element ID
        elemVMAP = VMAP.sElement(eset_definition.shape[1]-1)
        for ct_elem_definition, elem_definition in enumerate(eset_definition):
            elemVMAP.setIdentifier(int(elem_definition[0]))
            elemVMAP.setCoordinateSystem(coordinatesystem)
            elemVMAP.setMaterialType(mat_id)
            elemVMAP.setElementType(
                esettype_to_vmapelemtype[esets_types[ct_eset]])
            elemVMAP.setConnectivity(elem_definition[1:].tolist())
            elemBlock.setElement(ct_elem_definition, elemVMAP)
        outputfile.writeElementsBlock(part_group, elemBlock)
        print('done')

        # %%% esets_node_unique
        # get list of unique node IDs whithin this part. again, this is necessary because PERMAS models are always 'flat'.
        esets_nodes_unique.append(np.unique(eset_definition[:, 1:]))  # sorted!
        parts_numnodes[partnames[ct_eset]] = esets_nodes_unique[-1].shape[0]

        # %%% POINTS
        print('  POINTS ... ', end='')
        geomPoints = VMAP.sPointsBlock(esets_nodes_unique[-1].shape[0])
        ct_nd_all = -1
        for ct_eset_node, eset_node_id in enumerate(esets_nodes_unique[-1]):
            while True:
                ct_nd_all += 1
                if nodes_all_ids[ct_nd_all] == eset_node_id:
                    geomPoints.setPoint(ct_eset_node, int(
                        eset_node_id), nodes[ct_nd_all, 1:])
                    break
        outputfile.writePointsBlock(part_group, geomPoints)
        print('done')

        # %%% GEOMETRYSETS
        print('  GEOMETRYSETS for ...')
        geometrysetVector = VMAP.VectorTemplateGeometrySet()

        # %%%% NSETs to parts
        # convert esets_nodes_unique[-1] to set because 'in' operator is more efficient: https://wiki.python.org/moin/TimeComplexity
        print('    NSETS ...', end='')
        print_dots = False
        set_esets_nodes_unique = set(esets_nodes_unique[-1])
        for ct_nset, nset_first in enumerate(nsets_first):
            # TODO compare efficiency to 'if nset_first in esets_nodes_unique[-1]'
            if int(nset_first) in set_esets_nodes_unique:
                if print_dots == False:
                    print()
                print_dots = True
                print('      ' + nsets_names[ct_nset])
                myGeometrySet = VMAP.sGeometrySet()
                myGeometrySet.setSetType(
                    myGeometrySet.NODE_LOCATION)  # nodal geometry set
                myGeometrySet.setSetIndexType(
                    myGeometrySet.SINGLE_INDEX_TYPE)  # single value per entry
                myGeometrySet.setSetName(nsets_names[ct_nset])
                # this is unknown to PERMAS, it's just the chronological order of the NSET's in the model
                myGeometrySet.setIdentifier(ct_nset)
                myGeometrySet.setGeometrySetData(
                    [int(node) for node in nsets[ct_nset]])
                geometrysetVector.push_back(myGeometrySet)
        print('    ... done') if print_dots else print(' done')

        # %%%% SURFs to parts
        # convert eset to set because 'in' operator is more efficient: https://wiki.python.org/moin/TimeComplexity
        # assumption: surfs are w.r.t. one eset only
        print('    SURFACES ...', end='')
        set_eset = set(eset)
        print_dots = False
        for ct_surf, firstelem in enumerate(surfs_firstel):
            # TODO compare efficiency to 'if firstelem in eset' w/o set conversion
            if str(firstelem) in set_eset:
                if print_dots == False:
                    print()
                print_dots = True
                # here, we know the surface surfs[ct_surf] is in eset. is has the ID surfs_ids[ct_surf].
                # now we need to find the sfset containing this surface, via the latter's ID
                for ct_sfset, sfset_ids in enumerate(sfsets_ids):
                    if surfs_ids[ct_surf] in sfset_ids:
                        print('      ' + sfsets_names[ct_sfset] +
                              ' (surf_id ' + surfs_ids[ct_surf] + ')')
                        myGeometrySet = VMAP.sGeometrySet()
                        # element geometry set
                        myGeometrySet.setSetType(myGeometrySet.ELEMENT_LOCATION)
                        myGeometrySet.setSetIndexType(
                            myGeometrySet.PAIR_INDEX_TYPE)  # two values per entry
                        myGeometrySet.setSetName(
                            sfsets_names[ct_sfset] + '_' + surfs_ids[ct_surf])
                        myGeometrySet.setIdentifier(int(surfs_ids[ct_surf]))
                        myGeometrySet.setGeometrySetData(
                            [int(elem_or_face) for elem_or_face in surfs_flat[ct_surf]])  # TODO the result should be 2 dimensional
                        geometrysetVector.push_back(myGeometrySet)
        print('    ... done') if print_dots else print(' done')

        if geometrysetVector.size() > 0:
            outputfile.writeGeometrySets(part_group, geometrysetVector)
        print('  ... done')
    return parts_numnodes, esets_nodes_unique
