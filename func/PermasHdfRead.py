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
    The structure of the HDF file is: [component][situation][item][Data]

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
    HdfData : Pandas dataframe

    """
    if (keyword != "node_results") and (keyword != "model"):
        print("ERROR: Keyword does not exist!")
        sys.exit(1)

    HdfData = pd.DataFrame([])
    # component
    for i in range(len(list(openfile.keys()))):
        # read out types of components with .keys
        component = list(openfile.keys())[i]
        # can not open components starting with a dot (.)
        if component.startswith('.'):
            continue

        # SITUATIONS (e.g. DEFAULT)
        for j in range(len(list(openfile[component].keys()))):
            # read out types of situations with .keys
            situation = list(openfile[component].keys())[j]
            if situation.startswith('.'):
                # can not open situations starting with a dot (.)
                continue
            counter = 0
            # ITEM (e.g. CONTACT FORCE)
            for k in range(len(list(openfile[component][situation].keys()))):
                # read out types of items with .keys
                item = list(openfile[component][situation].keys())[k]

                # Model [COMPONENT][SITUATION][.Model]
                if keyword == "model":
                    # Read out ".Model"
                    if item.startswith('.Model'):
                        # save .Model in model
                        print('reading ' + openfile.filename + '/' +
                              component + '/' + situation + '/.Model',
                              flush=True)
                        HdfData = openfile[component][situation][item]
                        break
                # .Analysis and .Model do not have attribute keys
                if item.startswith('.'):
                    # cannot open items starting with a dot (.)
                    continue

                # DATA (e.g. .ColDes, .RowDes, Column1, Column2)
                for l in range(
                        len(list(openfile[component][situation][item].keys()))):
                    data = list(openfile[component][situation][item].keys())[l]

                    # NODE RESULTS [COMPONENT][SITUATION][RESULT][DATA]
                    if ((keyword == "node_results") and (item.startswith(variable_keyword))):
                        if data.startswith(".ColDes"):
                            print('reading ' + openfile.filename + '/' +
                                  component + '/' + situation + '/' + item +
                                  '/.ColDes', flush=True)
                            col_des = openfile[component][situation][item][data]
                            col_des = np.array(col_des)

                        if data.startswith('.RowDes'):
                            print('reading ' + openfile.filename + '/' +
                                  component + '/' + situation + '/' + item +
                                  '/.RowDes', flush=True)
                            row_hdf = openfile[component][situation][item][data]

                        for m in range(len(col_des)):
                            if data == 'Column%s' % int(m+1):
                                print('reading ' + openfile.filename + '/' +
                                      component + '/' + situation + '/' + item
                                      + '/' + data, flush=True)
                                counter = counter + 1
                                column_hdf = openfile[component][situation][item][data]
                                values = pd.DataFrame(np.array(column_hdf))
                                values.insert(0, 'node', np.array(row_hdf))
                                values.insert(1, "timestep", col_des[m])
                                values.insert(2, "variabletype", item)
                                if m == 0 and counter == 1:
                                    HdfData = values
                                else:
                                    HdfData = pd.concat(
                                        [HdfData, values], axis=0)
    return HdfData
