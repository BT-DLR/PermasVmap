"""
Function filtering the Permas-HDF for either model or nodal results.

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
import sys


def PermasHdfRead(openfile, keyword, variable_keyword='NONE'):
    """
    Read dataset(s) from Permas-HDF.

    Depending on the (variable_)keyword, the function reads a certain dataset.

    Depending on the analysis type of the situation, the returned dataset
    contains either a column 'timestep' or a column 'frequency', see the
    variables with prefix 'availableanalyses'

    The structure of the HDF file is: [component][situation][result_group][Data]
    ATM, only one component and one situation can be handled.

    Parameters
    ----------
    openfile : open VMAPFile
    keyword : string
        'model': read .Model dataset
        'node_results': read result dataset depending on variable_keyword
    variable_keyword : string, optional
        Name of Permas result quantity. The default is 'NONE'.

    Returns
    -------
    analysis_type : string
        Is empty if keyword == 'model'.
    HdfData : Pandas dataframe

    """
    if (keyword != 'node_results') and (keyword != 'model'):
        print('ERROR: keyword ' + keyword + 'does not exist!')
        sys.exit(1)

    # define implemented analysis types
    availableanalyses_temporal = ['STATIC', 'NLMATERIAL']
    availableanalyses_modal = ['VIBRATION ANALYSIS']

    # analysis type. actually there is one per situation, but only one situation is considered
    analysis_type = ''

    # return container
    HdfData = pd.DataFrame([])

    # COMPONENT
    ct_component = 0
    for component_str in openfile:
        # read out types of components with .keys
        # component = list(openfile.keys())[i]
        # ignore dataset .File Header
        if component_str.startswith('.'):
            continue
        else:
            print('  component: ' + component_str)
            component = openfile[component_str]
            ct_component += 1
        # only one component can be considered
        if ct_component > 1:
            print('WARNING: only one component possible, skipping '
                  + component_str + '.')
            continue

        # SITUATION
        ct_situation = 0
        for situation_str in component:
            if situation_str.startswith('.'):
                # if object starts with a dot (.), it is not a situation
                continue
            else:
                print('  situation: ' + situation_str)
                situation_path = openfile.filename + '/' + component_str + \
                    '/' + situation_str
                situation = component[situation_str]
                ct_situation += 1
                variable_path = situation_path + '/' + variable_keyword
            # only one situation can be considered
            if ct_situation > 1:
                print('WARNING: only one situation possible, skipping '
                      + situation_str + '.')
                continue

            # MODEL
            if keyword == 'model':
                try:
                    print('  reading ' + situation_path + '/.Model', flush=True)
                    HdfData = situation['.Model']
                except:
                    print('ERROR: no model found.')
                    sys.exit(1)
            # RESULTS
            else:
                # open result quantity requested by user
                if variable_keyword == 'NONE':
                    print('  user requests result keyword NONE -> finished')
                    break
                try:
                    result_group = situation[variable_keyword]
                except:
                    print('  NOTE: requested result keyword ' +
                          variable_keyword + ' not found.')
                    break
                # type of analysis
                try:
                    print('  reading ' + situation_path +
                          '/.Analysis', flush=True)
                    analysis_type = str(
                        situation['.Analysis'][:], sys.stdout.encoding).strip()
                    # the following comparisons are cumbersome due to using h5py 2.10 which is bad at reading strings
                    found_analysis_type = False
                    for availableanalysis in availableanalyses_temporal + availableanalyses_modal:
                        if analysis_type.startswith(availableanalysis):
                            analysis_type = availableanalysis
                            if not found_analysis_type:
                                print('  analysis: ' + analysis_type)
                            else:
                                print(
                                    'WARNING: found analysis type before, something might be wrong')
                            found_analysis_type = True
                    if not found_analysis_type:
                        print('ERROR: analysis type ' +
                              analysis_type + 'not available! Available analysis types: ', end='')
                        print(availableanalyses_temporal
                              + availableanalyses_modal)
                        sys.exit(1)
                except:
                    print('ERROR: no analysis found.')
                    sys.exit(1)
                # read .ColDes
                try:
                    col_des = np.array(result_group['.ColDes'])
                except:
                    print('ERROR: no dataset ' + situation_path +
                          '/' + variable_keyword + '/.ColDes')
                    sys.exit(1)
                # read .RowDes
                try:
                    row_des = np.array(result_group['.RowDes'])
                except:
                    print('ERROR: no dataset ' + variable_path + '/.RowDes')
                    sys.exit(1)
                # read Column1, Column2, etc and append to HdfData
                for ct_col, col_des_val in enumerate(col_des):
                    try:
                        print('  reading ' + variable_path +
                              '/Column' + str(ct_col+1), flush=True)
                        values = pd.DataFrame(
                            result_group['Column' + str(ct_col+1)])
                        # we have all we need. let's assemble our dataframe!
                        # column 'temporal' contains either timestep or frequency,
                        # repeated for every row (i.e. node)
                        values.insert(0, 'node', row_des)
                        values.insert(1, "temporal", col_des_val)
                        values.insert(2, "variabletype", variable_keyword)
                        if HdfData.size == 0:
                            HdfData = values
                        else:
                            HdfData = pd.concat(
                                [HdfData, values], axis=0)
                    except:
                        print('ERROR: cannot open column')
                        sys.exit(1)
    return analysis_type, HdfData
