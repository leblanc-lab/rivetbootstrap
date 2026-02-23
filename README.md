<h1>Rivet Bootstrap Script</h1>

[ToC]

## Introduction

This script provides a quick and convenient way to install Rivet and its core dependencies from the release tarball
or from source. It is designed to help users get up and running with a local build of Rivet: useful for development,
testing, or environments where package managers are unavailable or unsuitable. The script handles fetching, building,
and configuring all required components in a self-contained installation prefix.


## Basic usage

```
chmod a+x rivet-bootstrap
./rivet-bootstrap
```

This will install Rivet and its dependencies into `${PWD}/local`.

You can also enable the LHAPDF installation like so
```
INSTALL_LHAPDF=1 ./rivet-bootstrap
```
For additional options, see below.


## Prerequisites

This script assumes that standard development tools and build dependencies are already installed on your system,
including `libtool`, `automake`, `pkg-config`, and a C++ compiler with C++17 support.
It also requires `Python3`, `wget`, `zstd`, and basic Unix utilities.
These are typically available via your system package manager (e.g. `apt`, `dnf`, `brew`).
The script does not attempt to install these prerequisites automatically.

Note: Mac users should install the Xcode Command Line Tools using `xcode-select --install`.


## Configuration options

Additional script flags and their defaults:

### Build options

* `USE_CVMFS=0`: toggle to enable/disable using a suitable CMake/Python version from cvmfs if available
* `BUILD_PREFIX="$PWD"`: directory where the packages are to be downloaded and built
* `INSTALL_PREFIX="$PWD/local"`: directory where the packages are to be installed
* `PYTHON_EXE="python3"`: name of the Python executable to be used
* `USE_VENV="1"`: toggle to enable/disable the creation of a Python virtual environment
* `MAKE="make -j3"`: default make command to be used
* `CMAKE="cmake"`: name of the CMake executable to be used
* `PLUGIN_MATCH=""`: regex to match experiment group names to be selected at build time
* `PLUGIN_UNMATCH=""`: regex to unmatch experiment group names to be deselected at build time

### Package selection

* `INSTALL_LHAPDF="0"`: toggle to enable/disable the build of LHAPDF
* `INSTALL_HEPMC="1"`: toggle to disable/enable the build of HEPMC
* `INSTALL_FASTJET="1"`: toggle to disable/enable the build of FastJet
* `INSTALL_FJCONTRIB="1"`: toggle to disable/enable the build of fjcontrib
* `INSTALL_HDF5="1"`: toggle to disable/enable the build of HDF5
* `INSTALL_YODA="1"`: toggle to disable/enable the build of YODA
* `INSTALL_RIVET="1"`: toggle to disable/enable the build of Rivet
* `INSTALL_CYTHON="1"`: toggle to disable/enable the build of Cython

If a specific depedency build is disabled, it should be supplied as an external
dependency. The patch to the external installation directory can be specified
with the corresponding `PACKAGEPATH` flag. Simimarly, all of the packages come
with a `PACKAGE_VERSION` flag which can be used to specify the package version
directly.

### Build-from-source options

In order to build Rivet and YODA from source, you can toggle `INSTALL_RIVETDEV="0"`.
The variables `YODA_BRANCH` and `RIVET_BRANCH` can be used to specify the branches
explicitly.

### Additional config options for Rivet and YODA

Additional config options can be supplied for Rivet and YODA using
the `RIVET_CONFFLAGS` and `YODA_CONFFLAGS` variables.

