"""
Auxiliary functions.

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

import os
import sys

sep_big = '==========\n'
sep_small = '----------\n'

def check_argv(argv, list_suffix):
    """
    Check and process command line arguments Permas-HDF->VMAP.

    Parameters
    ----------
    argv : list of strings
        Command line arguments.
    list_suffix : list of strings
        Acceptable suffixes for input files.

    Returns
    -------
    self-explanatory

    """
    usage_string = '  Usage: python <this file> <Permas-HDF model filename within ./data> <optional_args_{1,2,3}>\n' + \
        '    optional_arg_1: Permas-HDF results filename within ./data\n' + \
        '    optional_arg_2: timesteps=1.0,2.0,... (list of floats. default: ALL)\n' + \
        '    optional_arg_3: variables_nodes=DISPLACEMENT,GAP_WIDTH,... (list of blank-less variables. default: ALL)\n'
    # check number of arguments
    if len(argv) == 1:
        print('ERROR: Wrong number of arguments, must be >1 .\n' + usage_string)
        sys.exit(1)
    INPUTFILENAME_model = argv[1]
    # check second argument's suffix: must match any of the entries of list_suffix
    INPUTFILENAME_model_split = INPUTFILENAME_model.split('.')
    len_argv_filenames = 2

    # at the second position an additional input file for results can be mentioned
    if len(argv) >= 3:
        if len(argv[2].split('=')) == 1:
            INPUTFILENAME_results = argv[2]
            # check second argument's suffix: must match any of the entries of list_suffix
            INPUTFILENAME_results_split = INPUTFILENAME_results.split(
                '.')
            len_argv_filenames = 3
    if len_argv_filenames == 2:
        # not generating an error down in the if because INPUTFILENAME_results_split has the wrong suffix
        INPUTFILENAME_results_split = [INPUTFILENAME_model_split[-1]]
        INPUTFILENAME_results = ''

    timesteps = ''
    variables_nodes = ''
    if len(argv) >= 3:
        for i in range(len(argv)-len_argv_filenames):
            if 'timesteps' in argv[i+len_argv_filenames]:
                timesteps = argv[i+len_argv_filenames].split('=')[1]
            elif 'variables_nodes' in argv[i+len_argv_filenames]:
                variables_nodes = argv[i+len_argv_filenames].split('=')[1]
            else:
                print('ERROR: Wrong number of arguments, must be >1 .\n' + usage_string)
                sys.exit(1)

    for suff in list_suffix:
        if INPUTFILENAME_model_split[-1] == suff and INPUTFILENAME_results_split[-1] == suff:
            return INPUTFILENAME_model, INPUTFILENAME_model_split, INPUTFILENAME_results, INPUTFILENAME_results_split, timesteps, variables_nodes
    print('ERROR: Wrong suffix of second argument, must be (any of) ' + str(list_suffix))
    sys.exit(1)


def check_argv_short(argv, list_suffix):
    """
    Check and process command line arguments VMAP->Permas-ASCII.

    Parameters
    ----------
    argv : list of strings
        Command line arguments.
    list_suffix : list of strings
        Acceptable suffixes for input files.

    Returns
    -------
    self-explanatory

    """
    # check number of arguments
    if len(argv) != 2:
        print('ERROR: Wrong number of arguments, must equal 2. Usage: python <this file> <input file name within ./data>')
        sys.exit(1)
    INPUTFILENAME = argv[1]

    # check second argument's suffix: must match any of the entries of list_suffix
    INPUTFILENAME_contituents = INPUTFILENAME.split('.')
    for suff in list_suffix:
        if INPUTFILENAME_contituents[-1] == suff:
            return INPUTFILENAME, INPUTFILENAME_contituents
    print('ERROR: Wrong suffix of second argument, must be (any of) ' + str(list_suffix))
    exit(1)


def assert_file_exists(filename):
    """Check if file exists."""
    if not os.path.exists(filename):
        print('File \'' + filename + '\' does not exist')
        sys.exit(1)
    return


def determine_times_vars(timesteps_user, variables_node_user, variable_nodes_exist):
    """
    Determine timesteps and variables that should be extracted.

    Parameters
    ----------
    timesteps_user : single string or multiple comma separated strings
        'NONE': read out no timestep (no variables!)
        'ALL': read out all timesteps (default option if not mentioned)
        1.0[,2.5,2.0,...]: read out the stated timesteps
    variables_node_user : single string or multiple comma separated strings
        'NONE': read out no node dependend variables
        'ALL': read out every possible variable dependend on nodes
        alternatives: DISPLACEMENT,CONTACT_STATUS,NODAL_POINT_STRAIN,
        NODAL_POINT_STRESS,GAP_WIDTH,TEMPERTAURE
    variable_nodes_exist : list of strings
        List of variables that can be handled.

    Returns
    -------
    timesteps_user : single string or multiple comma separated strings
    variables_node_user : single string or multiple comma separated strings

    """
    # determine the timesteps to read
    if timesteps_user == 'ALL':
        # every timestep
        timesteps_user = ['DEFAULT']
    elif timesteps_user == 'NONE':
        # no timestep
        timesteps_user == ['NONE']
    elif len(timesteps_user) == 0:
        # timesteps users not specified
        timesteps_user = ['DEFAULT']
    else:
        try:
            timesteps_user = timesteps_user.split(',')
            list_of_floats = []
            for timestep_user in timesteps_user:
                list_of_floats.append(float(timestep_user))
            timesteps_user = list_of_floats
        except ValueError:
            print(
                'ERROR: please insert a valid option for timesteps_user: ALL, NONE or timesteps 1.0,2.0,...')
            sys.exit(1)

    # detemine which nodal variable to read
    if variables_node_user == 'ALL':
        variables_node_user = variable_nodes_exist
    elif variables_node_user == 'NONE':
        variables_node_user = ['NONE']
    elif len(variables_node_user) == 0:
        variables_node_user = variable_nodes_exist
    else:
        variables_node_user = variables_node_user.split(',')
        for i in range(len(variables_node_user)):
            variables_node_user[i] = variables_node_user[i].replace('_', ' ')
            if variables_node_user[i] not in variable_nodes_exist:
                print('ERROR: variable name %s not valid, please add variable type to variable_nodes_exist' % (
                    variables_node_user[i]))
                quit()

    # return
    return timesteps_user, variables_node_user
