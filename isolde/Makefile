# The "make" targets are:
# 	wheel: build a Python wheel in "dist" directory.
# 	app-install: build wheel (if needed) and install in ChimeraX
# 	clean: remove files used in building wheel

# CHIMERAX_APP should be the ChimeraX install folder
CHIMERAX_APP = /home/tic20/apps/chimerax

# These bundle data may be changed as needed.
# By convention, ChimeraX bundles start with "ChimeraX-"
# and the ChimeraX toolshed code apparently really wants
# the "chimerax." part of the package name (for now).
BUNDLE_NAME = ChimeraX-ISOLDE
BUNDLE_VERSION = 0.9.1
PKG_NAME = chimerax.isolde

# Source and data files.  By default, all .py files
# except for setup.py and no data files.
PYSRCS = $(filter-out setup.py,$(wildcard *.py))
DATAFILES = 

# ==================================================================
# Theoretically, no changes should be needed below here.

# Platform-dependent settings.  Should not need fixing.
# For Windows, we assume Cygwin is being used.
OS = $(patsubst CYGWIN_NT%,CYGWIN_NT,$(shell uname -s))
ifeq ($(OS),CYGWIN_NT)
PYTHON_EXE = $(CHIMERAX_APP)/bin/python.exe
CHIMERAX_EXE = $(CHIMERAX_APP)/bin/ChimeraX.exe
endif
ifeq ($(OS),Darwin)
PYTHON_EXE = $(CHIMERAX_APP)/Contents/bin/python3.5
CHIMERAX_EXE = $(CHIMERAX_APP)/Contents/bin/ChimeraX
endif
ifeq ($(OS),Linux)
PYTHON_EXE = $(CHIMERAX_APP)/bin/python3.5
CHIMERAX_EXE = $(CHIMERAX_APP)/bin/ChimeraX
endif
COPY = cp -r

# Paths used for constructing the installation "wheel"
PKG_PATH = $(shell echo $(PKG_NAME) | sed 's,\.,/,'g)
PKG_DIR = build/src/$(PKG_PATH)
ifeq ($(OS),CYGWIN_NT)
PKG_DIR := $(shell cygpath -m '$(PKG_DIR)' | sed 's,/,\\\\\\\\,g')
endif
WHL_BNDL_NAME = $(subst -,_,$(BUNDLE_NAME))
WHEEL = dist/$(WHL_BNDL_NAME)-$(BUNDLE_VERSION)-py3-none-any.whl

#
# Actual make dependencies!
#

wheel $(WHEEL): $(PKG_DIR) $(PYSRCS) setup.py
	$(PYTHON_EXE) setup.py --no-user-cfg bdist_wheel
	rm -rf $(WHL_BNDL_NAME).egg-info

app-install:	$(WHEEL)
	$(CHIMERAX_EXE) -m pip install -U $(WHEEL)

setup.py: setup.py.in Makefile
	sed -e 's,PKG_DIR,$(PKG_DIR),' \
		-e 's,BUNDLE_NAME,$(BUNDLE_NAME),' \
		-e 's,BUNDLE_VERSION,$(BUNDLE_VERSION),' \
		-e 's,PKG_NAME,$(PKG_NAME),' \
		-e 's,PKG_DIR,$(PKG_DIR),' \
		< setup.py.in > setup.py

$(PKG_DIR):	$(PYSRCS) $(DATAFILES)
	if [ ! -d "$(PKG_DIR)" ]; then mkdir -p $(PKG_DIR); fi
	$(PYTHON_EXE) -B -m py_compile $(PYSRCS)
	$(COPY) $(PYSRCS) $(DATAFILES) $(PKG_DIR)

clean:
	rm -rf __pycache__ build dist $(WHL_BNDL_NAME).egg-info setup.py