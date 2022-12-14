"""
Function for reading Permas results.

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
from . import PermasHdfRead


def PermasResultsRead(inputfile_results, timesteps_user, variables_node_user):
    """
    Read Permas results. Only nodal results can be processed.

    Principle: read results into one large Pandas (pd) DataFrame. Then, apply
    pd high-level functions. This is probably a good compromise between ease of
    implementation and efficiency. For higher efficiency, avoid pd and use only
    low-level operations.

    Parameters
    ----------
    inputfile_results : open HDF file
    timesteps_user : list of strings
    variables_node_user : list of strings
        The exaxt names of the Permas results.

    Returns
    -------
    timesteps_list : list of floats
        Actual timesteps of returned results, sorted ascendingly.
    variablestypes_nodes_list : list of strings
        Actual variable names of returned results, in alphabetical order.
    node_results_pd : pd dataframe
        Cols: nodal id, timestep value, variable name, value (6x), partname.

    """
    print('READING RESULTS')
    if 'NONE' in timesteps_user:
        node_results_pd = pd.DataFrame([])

    # READ NODAL RESULTS
    if 'NONE' in variables_node_user:
        node_results_pd = pd.DataFrame([])
    else:
        if not 'DEFAULT' in variables_node_user:
            for i in range(len(variables_node_user)):
                node_results_var = PermasHdfRead.PermasHdfRead(
                    inputfile_results, 'node_results', variable_keyword=variables_node_user[i])
                if i == 0:
                    node_results_pd = node_results_var
                else:
                    node_results_pd = pd.concat(
                        (node_results_pd, node_results_var), axis=0)
            # only needed timesteps:
            if not 'DEFAULT' in timesteps_user:
                node_results_pd = node_results_pd[node_results_pd.timestep.isin(
                    timesteps_user)]
        else:
            node_results_pd = []

    # determine the different timesteps and variabletypes for the results
    try:
        variablestypes_nodes_list = sorted(
            list(set(node_results_pd.variabletype)))
    except AttributeError:
        variablestypes_nodes_list = []
    print('node dependend variables:', variablestypes_nodes_list)
    print()

    try:
        timesteps_list = sorted(list(set(node_results_pd.timestep)))
    except AttributeError:
        timesteps_list = []

    return timesteps_list, variablestypes_nodes_list, node_results_pd
