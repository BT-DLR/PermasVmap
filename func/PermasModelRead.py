"""
Functions for the model.

Reading the dataset .Model from Permas-HDF and extracting GEOMETRY, SYSTEM,
MATERIAL data.

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
import itertools
import sys
from . import PermasHdfRead


def print_readline(line_split):
    """Print the current line that has been split."""
    print('extracting ' + ' '.join(line_split), end='', flush=True)


def flatten_sets(list_3level):
    """
    Flatten 2 levels  of nested lists, using itertools: https://datascienceparichay.com/article/python-flatten-a-list-of-lists-to-a-single-list/ .

    Parameters
    ----------
    list_3level : list of lists of lists

    Returns
    -------
    list_2level : list of lists
        The lowest hierarchy of list_3level is flattened while the top-level is
        preserved.

    """
    list_2level = [None] * len(list_3level)
    for ct_set, mylist in enumerate(list_3level):
        list_2level[ct_set] = list(itertools.chain(*mylist))
    return list_2level


def PermasModelRead(inputfile_model):
    """
    Read the permas model (dataset .Model) as a list and then parse it.

    Parameters
    ----------
    inputfile_model : Opened HDF file

    Returns
    -------
    nodes : np.array of float64
        num-nodes x 4, first col is node index, remaining cols are coordinates
    esets : list of lists of strings
        Element indexes of each eset, same order as partnames.
    partnames : list of strings
        Names of parts, same order as eset.
    elements_hexe8 : np.array of int32
        num-elems-hexe8 x 9, first col is element index, remaining cols are
        defining nodes
    elements_tet10 : np.array of int32
        num-elems-tet10 x 11, first col is element index, remaining cols are
        defining nodes
    sfsets_names : list of strings
        Names of sfsets, same order as sfsets_ids.
    sfsets_ids : list of lists of strings
        Definitions of sfsets referring surfs_ids, same order as sfsets_names.
    surfs_ids : list of strings
        Indexes of surfs, same order as surfs.
    surfs : list of lists of lists of two strings
        Zeroth dimension: each entry represents one surf.
        First dimension: contains surf definition.
        Second dimension: contains an element index and that element's face
        index.
    surfs_flat : list of lists of strings
        Flattened version of surfs: the deepest two levels are merged. Element
        index and corresponding face index are alternating.
    nsets : list of lists of strings
        List containing one list of nodal indices for each nset. Same order as
        nset_names.
    nsets_names : list of strings
        Contains the names of the nsets. Same order as nsets.
    materials : list of dictionaries
        For each material there is one dictionary with the keys 'name', 'id',
        'modulus', 'poisson', 'density'.
    eset_material : dictionary
        Relates partnames to materials.
    coorsystems : list of lists of floats
        One list per cylindrical coordinate system. Contains all numerical
        values of the definition in chronological order.

    """
    print('READING DATA')
    # %% prepare

    model_h5dataset = PermasHdfRead.PermasHdfRead(inputfile_model, 'model')

    # change datatype from h5py._hl.dataset.Dataset to numpy.ndarray to list
    # https://www.w3resource.com/numpy/string-operations/decode.php
    model_list = list(np.char.decode(model_h5dataset, encoding='UTF-8'))

    del(model_h5dataset)

    # result containers
    nodes = []
    elements_hexe8 = []
    elements_tet10 = []
    esets = []
    partnames = []  # part = eset if it is HEXE8 or TET10
    nsets = []
    nsets_names = []
    sfsets_names = []
    sfsets_ids = []
    surfs_ids = []
    surfs = []

    # positions of definitions of 'complex' data
    material_position = []
    coorsys_position = []
    elprop_position = []

    # containers for 'complex' data
    materials = []
    coorsystems = []
    eset_material = {}  # this will contain pairs ESET:MATERIAL

    # %% read 1
    # here, most quantities are read out, such as coordinates, elements, etc.
    # but NOT more complicated data structure such as materials and coor sys.
    # however, we will remember the positions at which the latter are located

    current_data = None  # this will point to the above containers or to their future contents
    current_data_name = None

    # main loop. paradigm: process each line exactly once
    for ct_line, line in enumerate(model_list):
        line_split = line.lstrip().split()
        line_is_data = line_split[0].isdecimal() or line_split[0] == '&'
        if current_data != None:  # this is needed because there might be data blocks that are ignored
            if line_split[0].isdecimal():  # we have a data line
                current_data.append(line_split)
            elif line_split[0] == '&':  # we have a continued data line
                current_data[-1] += line_split[1:]
            else:  # i.e. line_is_data == False
                if not current_data_name == None:
                    print(' ... done')
                    current_data_name = None
        if not line_is_data:
            # set current_data to whichever container is appropriate
            if line_split[0] == '$COOR':
                current_data = nodes
                current_data_name = '$COOR'
                print_readline(line_split)
            elif line_split[0] == '$ELEMENT':
                if line_split[-1] == 'HEXE8':
                    current_data = elements_hexe8
                    current_data_name = '$ELEMENT HEXE8'
                    print_readline(line_split)
                elif line_split[-1] == 'TET10':
                    current_data = elements_tet10
                    current_data_name = '$ELEMENT TET10'
                    print_readline(line_split)
                else:
                    print('skipping ' + ' '.join(line_split), flush=True)
                    current_data = None
                    current_data_name = ''
            elif line_split[0] == '$ESET':
                esets.append([])
                current_data = esets[-1]
                current_data_name = line_split[-1]
                partnames.append(line_split[-1])
                print_readline(line_split)
            elif line_split[0] == '$NSET':
                nsets.append([])
                current_data = nsets[-1]
                current_data_name = line_split[-1]
                nsets_names.append(line_split[-1])
                print_readline(line_split)
            elif line_split[0] == '$SURFACE':
                surfs.append([])
                current_data = surfs[-1]
                current_data_name = line_split[-1]
                surfs_ids.append(line_split[4])
                print_readline(line_split)
            elif line_split[0] == '$SFSET':
                sfsets_ids.append([])
                current_data = sfsets_ids[-1]
                current_data_name = line_split[-1]
                sfsets_names.append(line_split[-1])
                print_readline(line_split)
            elif line_split[0] == '$MATERIAL':
                material_position.append(ct_line)
            elif line_split[0] == '$RSYS':
                coorsys_position.append(ct_line)
            elif line_split[0] == '$ELPROP':
                elprop_position.append(ct_line)
            else:
                current_data = None
    print()

    # %%% flatten 3-level lists
    # 3-level lists are flattened s.t. each of them is a list of lists (wich no further lower level lists)
    esets = flatten_sets(esets)
    nsets = flatten_sets(nsets)
    sfsets_ids = flatten_sets(sfsets_ids)
    surfs_flat = flatten_sets(surfs)

    # %% read 2
    # here, the complex quantities are read

    # %%% MATERIAL
    for ct_mat, mat_pos in enumerate(material_position):
        # header
        line_split = model_list[mat_pos].lstrip().split()
        if not 'NAME' in line_split:
            print('WARNING: material has no name. skipping line: ' +
                  model_list[mat_pos])
            continue
        if not 'ISO' in line_split:
            print('WARNING: material is not ISO, which has not been tested')
        materials.append({'name': line_split[3], 'id': ct_mat})
        print('extracting material ' +
              materials[-1]['name'] + ' ... ', end='')

        # body
        pos_offset = 1
        line_split = model_list[mat_pos+pos_offset].lstrip().split()
        while not line_split[0] == '$END':
            line = model_list[mat_pos+pos_offset].lstrip()
            if line == '$ELASTIC  GENERAL  INPUT = DATA':
                pos_offset += 1
                materials[-1]['modulus'] = float(
                    model_list[mat_pos + pos_offset].lstrip().split()[0])
                materials[-1]['poisson'] = float(
                    model_list[mat_pos + pos_offset].lstrip().split()[1])
            elif line.startswith('$ELASTIC'):
                print('WARNING: unknown $ELASTIC block, continuing')
            elif line == '$DENSITY  GENERAL  INPUT = DATA':
                pos_offset += 1
                materials[-1]['density'] = float(
                    model_list[mat_pos + pos_offset].lstrip().split()[0])
            elif line.startswith('$DENSITY'):
                print('WARNING: unknown $DENSITY block, continuing')
            pos_offset += 1
            line_split = model_list[mat_pos+pos_offset].lstrip().split()
        print('... done')
    print()

    # %%% ELPROP
    for elprop_pos in elprop_position:
        print('extracting ELPROP block ... ')
        pos_offset = 1
        line_split = model_list[elprop_pos+pos_offset].lstrip().split()
        while not (line_split[0].startswith('$') or line_split[0].startswith('!')):
            if line_split[1] == 'MATERIAL':
                # add pair PART:MATERIAL to dictionary eset_material
                eset_material[line_split[0]] = line_split[-1]
                print('  ' + line_split[0] + ': ' + line_split[-1])
            pos_offset += 1
            line_split = model_list[elprop_pos+pos_offset].lstrip().split()
        print('... done')
    print()

    # %%% RSYS
    for coorsys_pos in coorsys_position:
        print('extracting RSYS block ... ')
        pos_offset = 1
        line_split = model_list[coorsys_pos+pos_offset].lstrip().split()
        while not (line_split[0].startswith('$') or line_split[0].startswith('!')):
            if line_split[0].isdecimal():  # begin of coordinate system def
                coorsystems.append([])
                # exclude ending colon. assumption: entry is number if it begins with a digit or a minus sign
                coorsystems[-1] += [float(number) for number in line_split if (
                    number[0].isdecimal() or number[0] == '-')]
                pos_offset += 1
                line_split = model_list[coorsys_pos+pos_offset].lstrip().split()
            elif line_split[0] == '&':
                del line_split[0]
                coorsystems[-1] += [float(number) for number in line_split if (
                    number[0].isdecimal() or number[0] == '-')]
                pos_offset += 1
                line_split = model_list[coorsys_pos+pos_offset].lstrip().split()
            else:
                print('ERROR: this should not be reached')
                sys.exit(1)

    # %% return
    print()

    return \
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
        coorsystems
