"""
Function for postprocessing of Permas model data.

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
import sys


def PermasModelPostprocess(
        nodes,
        esets,
        partnames,
        elements_hexe8,
        elements_tet10,
        surfs_ids,
        surfs,
        nsets):
    """
    Postprocess some model quantities from PermasModelRead.

    Parameters
    ----------
    see PermasModelRead

    Returns
    -------
    nodes : array of float64
    esets : list of lists of strings
        Only contains the esets of certain element types. Same order as
        partnames.
    partnames : list of strings
        Partnames corresponding to cleaned-up version of esets.
    elements_hexe8 : array of int32
    elements_tet10 : array of int32
    nodes_all_ids : array of int32
        Sorted indices of all nodes.
    esets_types : list of strings
        Element types of esets. Same order as cleaned esets.
    elements_hexe8_ids : array of int32
        Sorted indices of all HEXE8.
    elements_tet10_ids : array of int32
        Sorted indices of all TET10.
    nsets_first : list of strings
        First element of every nset.
    surfs_firstel : list of strings
        First element of every surf definition.

    """
    print('POSTPROCESSING READ DATA')

    # convert nodes end elements to most appropriate numpy arrays
    nodes = np.array(nodes, dtype=np.float64)
    elements_hexe8 = np.array(elements_hexe8, dtype=np.int32)
    elements_tet10 = np.array(elements_tet10, dtype=np.int32)

    # rearrange tet10 from PERMAS to VMAP definition
    tet10_vmap = [0] * 10
    for tet10_permas in elements_tet10:
        tet10_vmap[0] = tet10_permas[1]
        tet10_vmap[4] = tet10_permas[2]
        tet10_vmap[1] = tet10_permas[3]
        tet10_vmap[5] = tet10_permas[4]
        tet10_vmap[2] = tet10_permas[5]
        tet10_vmap[6] = tet10_permas[6]
        tet10_vmap[7] = tet10_permas[7]
        tet10_vmap[8] = tet10_permas[8]
        tet10_vmap[9] = tet10_permas[9]
        tet10_vmap[3] = tet10_permas[10]

        tet10_permas[1:] = tet10_vmap

    # get IDs in dedicated array for efficient access (np.array's default is c-contiguous)
    nodes_all_ids = np.array(nodes[:, 0], dtype=np.int32)
    elements_hexe8_ids = elements_hexe8[:, 0] if elements_hexe8.ndim == 2 \
        else []
    elements_tet10_ids = elements_tet10[:, 0] if elements_tet10.ndim == 2 \
        else []

    # clean partnames_temp: esets_temp are parts iff they consist of HEXE8 or TET10
    # assumption: esets_temp consist of homogeneous element type, i.e. it suffices to check only the first element's type
    print('cleaning parts and asserting types of esets ... ')
    esets_temp = []
    esets_types = []
    partnames_temp = []
    for ct_eset, eset in enumerate(esets):
        if int(eset[0]) in elements_hexe8_ids:
            esets_temp.append(eset)
            partnames_temp.append(partnames[ct_eset])
            esets_types.append('HEXE8')
            print('  part ' + partnames_temp[-1] +
                  ' has element type ' + esets_types[-1])
        elif int(eset[0]) in elements_tet10_ids:
            esets_temp.append(eset)
            partnames_temp.append(partnames[ct_eset])
            esets_types.append('TET10')
            print('  part ' + partnames_temp[-1] +
                  ' has element type ' + esets_types[-1])
        else:
            print('  eset ' + partnames[ct_eset] +
                  ' is removed from list of parts')
    esets = esets_temp
    partnames = partnames_temp
    print('... done')

    # define nsets_first: list of first elements of nsets
    nsets_first = [None] * len(nsets)
    for nset_id, nset in enumerate(nsets):
        nsets_first[nset_id] = nset[0]

    # define surfs_firstel: list of first elements of surfs
    surfs_firstel = [None] * len(surfs)
    for surf_id, surf in enumerate(surfs):
        surfs_firstel[surf_id] = surf[0][0]

    # check if surfaces belong to parts. throw error if they don't
    # assumption: surfaces are defined within one eset only, i.e. it suffices to check only the surface's first element
    print('assuring that all surfaces belong to parts ... ', end='')
    for surf_id, surf in enumerate(surfs):
        if not (surf[0][0] in eset for eset in esets):
            print('\nERROR: surface with ID ' +
                  surfs_ids[surf_id] + ' does not belong to any part. this case is not yet implemented.')
            sys.exit(1)
    print('done')

    print()

    return nodes, \
        esets, \
        partnames, \
        elements_hexe8, \
        elements_tet10, \
        nodes_all_ids, \
        esets_types, \
        elements_hexe8_ids, \
        elements_tet10_ids, \
        nsets_first, \
        surfs_firstel
