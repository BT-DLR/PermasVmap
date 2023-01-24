# General
All sorts of contributions are welcome: code, feature requests, bug reports, use cases, ...

## Support
Open an issue in the Github repository.

## Roadmap
Current wishlist in random order:
- PENTA15, CONA4, CONA6 elements
- Consideration of extrapolation strategy for second order elements
- More material properties: thermal properties, temperature dependence
- Increase efficiency handling FE results by substituting low-level operations for Pandas Dataframe operations
- Increase efficiency assigning nodes to parts (current bottleneck, although already fairly optimized)
- Fix conversion of cylindrical coordinate systems
- Automatic global cartesian coordinate system, correctly referred to by ELEMENTS
- Adaptive output data types (should not be 64-bit if inputs are 32-bit)

# Getting started in Sypder 5 IDE
0. If you don't have Spyder at hand, you may install it via [conda](https://anaconda.org/anaconda/spyder).
1. Set your Python interpreter to the one in the correct environment: Tools -> Preferences -> Python interpreter. Make sure to have the correct version of the module `spyder-kernels` available, otherwise Spyder will tell you in the IPython console.
2. Change the console directory to the repository root.
3. Execute `runfile('Permashdf2Vmap.py', args='rotorsegment.hdf')`

# Contributing

## Location of files
The main script files are in the repository's root directory. All functions go into [/func](/func). Input data goes into [/data](/data), which is also where the output will be written.

## Repository hygiene
Be careful including new data files in order to keep the repository size low.

Take care of [.gitignore](.gitignore).

## Code style

### Code format
- Conform to [PEP 8](https://peps.python.org/pep-0008) convention. The code is currently developed in Spyder 5 with built-in _autopep8_ autoformat on save.
- Indentation is 4 spaces.
- Line length for non-comments should not exceed 80 characters.
- Nympy docstrings
- End of line character EOL: Windows style (CR LF, `\r\n`)
- If function arguments, return values or the assignments of the latter are too long for a one-liner, separate the values into one item per line using line continuation `\`.

### Comments
The code is developed in Spyder 5 and uses the special comments `# %%`, `# %%%`, ... in order to keep the outline browser useful.

Use Numpy docstrings for functions. (In Spyder: right-click on a function name and choose 'Generate docstring' for a template)

### Naming
File names and function names are in camel case. Variable names are in lower case and use underscores as logical separators. Logical "hierarchies" of variables is reflected in the names, e.g. `elements_tet10` contains the element definitions and `elements_tet10_ids` contains only the indices of the former, i.e. the first column of element definitions.

Counters (e.g. in `for` loops on `enumerate`d quantities) are prefixed `ct_`.

## Paradigms

### Efficiency
Performance must always be in mind when implementing new features. What happens to the runtime and the memory if you increase the number of nodes or elements by 1000x? Where is the bottleneck?

This is rather general but while we're at it:
- Try to avoid loading or storing data. If not unavoidable, re-use it instead of re-computing or re-reading it from the hard drive.
- Access data linearly: no 'jumping around'.
- Use iterators on containers instead of looping an index variable through its range (also more readability and less room for errors).
- Use low-level Python features for low-level code hierarchy: the more often you perform an operation (e.g. on FE nodes, the lowest-level objects) the more care you should take with respect to efficiency.
- Avoid conversion of types, as they often lead to deep-copies of the data.
- Use static typing where it is worth: if you have a large set of numerical values in rectangular shape (i.e. matrix or vector) _and_ know the data type is homogeneous, then use numpy arrays with explicit, economical dtype.

### Functions vs script
Prefer functional architecture over script-like design, even if re-use of the function is unlikely/impossible. Given the size of the program, a functional design increases readability and eases understanding the code. Only the main files are scripts, accepting command line arguments.

### Why use Permas-HDF and not Permas-ASCII (.dat) for the FE model?
We've tried going Permas-ASCII only, i.e. even as input for main workflow 1 if there is just a model with no results. We decided to avoid this route for the following reasons:

1. It is quite tedious to consider all possibilities when parsing Permas-ASCII, given the rather loose Permas input specification. In contrast, Permas-HDF offers a reliable model format, although it is only pseudo-tabular and needs to be parsed nonetheless. But the parsing is easily done and robustness is for free.
2. For conversion of the FE results, the Permas-HDF format is the natural choice. Therefore Permas-HDF would be required for the results anyway and we believe it is reasonable to extend this requirement to the model.
