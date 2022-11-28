[![DOI](https://zenodo.org/badge/570393646.svg)](https://zenodo.org/badge/latestdoi/570393646)

# PermasVmap

A converter from Permas to VMAP and vice versa.

## What's this
This software converts **models and results** from the Finite Element software **[Permas](https://www.intes.de/?neue_sprache=en)** to **[VMAP](https://vmap.vorschau.ws.fraunhofer.de)** and back. It is written in Python with automated applications in mind, such as cross-disciplinary optimization. The initial focus is on 3D scenarios with solid volume elements only but extensions to other kinds of elements (shells etc.) are envisioned.

### Why use VMAP?
In our view, VMAP provides two critical features that cannot be found elsewhere
1. **Central** conversion data format. It provides **interfaces to more than 25 simulation softwares**, and counting.
2. **Standardized** [HDF5](https://www.hdfgroup.org/solutions/hdf5) format specification that is productive for structural FE simulations. The fact that **both models and results are machine accessible without parsing ASCII**, using open source software only, enables much needed efficiency at low entry barriers.

## Key features
1. **Performance**. The code was optimized for speed and tested on a model with more than 4.2 million second order tetrahedral elements. On a standard desktop computer the overall process time for the conversion of the Permas model to the VMAP format takes just over 2 minutes. This is actually not bad because *Permas models lack the part hierarchy level, so the costly association of nodes to parts has to be conducted by the converter*. At the moment there is no use of parallel computation.
2. **Reliability**. The code is tested end-to-end at [DLR](https://dlr.de) using multiple non-academic test models.

## Detailed list of features
1. Supported elements: HEXE8, TET10
2. Further supported model keywords:
   - $NSET (assumption: each NSET is contained in one ESET)
   - $SURFACE ELEMENTS (assumption: each SURFACE is contained in one ESET)
   - $SFSET
   - $MATERIAL with $ELASTIC GENERAL (no temperature dependence) and $DENSITY
   - $ELPROP with MATERIAL
   - $RSYS (not fully functional yet)
   
## Main workflows
1. (Permas-ASCII ->) Permas-HDF -> VMAP
   - for FE model and/or results
   - the first step (model only) needs to be done by Permas, see next section.
   - for the second step see PermasHdf2Vmap.py
2. VMAP -> Permas-ASCII
   - for FE model only
   - see Vmap2PermasAscii.py

## Getting started _using_ the code

### Requirements
- VMAP v1.0.0
- Python envionment according to [environment.yml](./environment.yml)

### Instructions
1. Set up a python environment including the modules listed in [environment.yml](./environment.yml), e.g. using [conda](https://conda.io).
2. Copy the file [./local/local_imports.py.template](local/local_imports.py.template) to _./local_imports.py_ and adapt it so that you local VMAP instance is found.
2. Activate the environment, change to the code's root directory and run `python Permashdf2Vmap.py rotorsegment.hdf`.
3. See the result in the [data](/data) subfolder: the input file [rotorsegment.hdf](/data/rotorsegment.hdf) was converted to _rotorsegment_toVMAP.hdf_ according to the VMAP standard.
4. run `python Vmap2PermasAscii.py rotorsegment_toVMAP.hdf` for the inverse conversion.
5. See the result in the [data](/data) subfolder: the input file _rotorsegment_toVMAP.hdf_ was converted to _rotorsegment_toVMAP_toPERMASASCII.dat_.
6. For more info on the usage, run `python Permashdf2Vmap.py` or `python Vmap2PermasAscii.py` to see explanations and examples of the possible arguments.
7. The input file for main workflow 1 must be in Permas-HDF format. If you just have an ASCII version of your model, use Permas to convert it to Permas-HDF via a UCI file with the following content:

```
SET DATABASE = DELETE

NEW
INPUT
	READ PERMAS FILE = my_permas_model.dat
RETURN

TASK
	EXPORT
		MODEL
		GO PERMAS BINARY
TASK END
STOP
```

## Getting started _contributing to_ or _adapting_ the code
See [CONTRIBUTING.md](CONTRIBUTING.md). There you can also find information on the reasonig behind features, workflows etc.

## Authors and acknowledgment
Nadine Barth and Oliver Kunc were the initial main developers.

## License
Licensed under the Apache License, Version 2.0, see [LICENSE](LICENSE).

## Project status
Development of this project is **active** (2022). Contributions are highly welcome, see [CONTRIBUTING.md](CONTRIBUTING.md) for more information.
