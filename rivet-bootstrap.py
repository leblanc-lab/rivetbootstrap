#! /usr/bin/env python

## $Date: 2009-03-17 16:31:08 +0000 (Tue, 17 Mar 2009) $
## $Revision: 1394 $

## TODO: Make it possible to run without internet access if expanded tarballs are already in place

import os, sys, logging, shutil
from optparse import OptionParser

DEFAULTPREFIX = os.path.join(os.cwd(), "local")

parser = OptionParser()
parser.add_option("--prefix", metavar="INSTALLDIR", default=DEFAULTPREFIX, dest="PREFIX", 
                  help="Location to install packages to")
parser.add_option("--devmode", action="store_true", default=False, dest="DEV_MODE", 
                  help="Use the SVN development head version of Rivet")
parser.add_option("--ignore-afs", action="store_true", default=False, dest="IGNORE_AFS", 
                  help="Always bootstrap from sources, even if AFS versions are available")
parser.add_option("--rivet-version", default="1.1.3a0", dest="RIVET_VERSION", 
                  help="Explicitly specify version of Rivet to get and use")
parser.add_option("--hepmc-version", default="2.04.01", dest="HEPMC_VERSION", 
                  help="Explicitly specify version of HepMC to get and use")
parser.add_option("--fastjet-version", default="2.4.0", dest="FASTJET_VERSION", 
                  help="Explicitly specify version of FastJet to get and use")
parser.add_option("--boost", metavar="DIR", default="", dest="BOOST_DIR", 
                  help="Explicit path to find Boost")
parser.add_option("--install-boost", action="store_true", default=False, dest="INSTALL_BOOST", 
                  help="Don't use a system copy of Boost (NB. it takes a long time to build)")
parser.add_option("--boost-version", default="1_38_0", dest="BOOST_VERSION", 
                  help="Explicitly specify version of Boost to get and use (if --install-boost is used)")
parser.add_option("-V", "--verbose", action="store_const", const=logging.DEBUG, dest="LOGLEVEL",
                  default=logging.INFO, help="print debug (very verbose) messages")
parser.add_option("-Q", "--quiet", action="store_const", const=logging.WARNING, dest="LOGLEVEL",
                  default=logging.INFO, help="be very quiet")
opts, args = parser.parse_args()


## Configure logging
try:
    logging.basicConfig(level=opts.LOGLEVEL, format="%(message)s")
except:
    logging.getLogger().setLevel(opts.LOGLEVEL)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger().addHandler(h)


## Build and install to the PREFIX location
PREFIX = os.path.abspath(opts.PREFIX)
if not os.path.exists(PREFIX):
    os.makedirs(PREFIX)
if not os.access(os.W_OK, PREFIX):
    logging.error("Can't write to installation directory, %s... exiting" % PREFIX
    sys.exit(1)
fi


# ## Set up Python install area
# logging.verbose("Setting up Python library install area: must exist and be in $PYTHONPATH")
# pyversion =  "%d.%d" % (sys.version_info[0], sys.version_info[1])
# pylibdir = os.path.join(PREFIX, "lib", "python%s/site-packages" % pyversion)


## Function to unpack and delete a tarball
def get_tarball():
                      
    echo "Downloading: $WGETTER $1 | tar xzv"
    ($WGETTER $1 | tar xzv) || exit 1
}


## Function to enter an expanded tarball and run the usual
## autotools ./configure, make, make install mantra
conf-mk-mkinst() {
    if test -d $1; then
        (cd $1 && echo "./configure --prefix=$PREFIX" && \
            ./configure --prefix=$PREFIX --enable-shared $2 && \
            make && make install) || exit 2
    else
        echo "Couldn't find $1... exiting"
        exit 1
    fi
}


##############################


## Get Rivet either from released tarballs or SVN
if test "$DEVELOPERMODE" != "yes"; then
    ## USER MODE
    ## Get Rivet tarball (for non-developers)
    RIVET_NAME=Rivet-$RIVET_VERSION
    RIVET_URL=http://www.hepforge.org/archive/rivet/$RIVET_NAME.tar.gz
    echo "Getting $RIVET_URL"
    wget-untargz $RIVET_URL
    ln -s $RIVET_NAME rivet || exit 2

else

    ## DEVELOPER MODE
    ## If we've got SVN and there is no already-checked out version
    ## of Rivet in this directory, then check out/update
    ## the SVN head versions using the HTTP access method
    for pkg in svn autoconf autoreconf automake libtool; do
        if test ! -x "`which $pkg 2> /dev/null`"; then
            echo "You must have $pkg installed to bootstrap in developer mode" 1>&2
            exit 1
        fi
    done

    if [[ ! -e rivet ]]; then 
        svn co http://svn.hepforge.org/rivet/trunk rivet || exit 2        
	else
	    svn update rivet
    fi
    if [[ -e rivet && ! -e rivet/configure ]]; then 
        (cd rivet && autoreconf -i) || exit 2
    fi

fi


## Build Python HepMC interface if required
if test "$USE_PYTHON" == "yes"; then
    echo "Building Python HepMC interface"
    PYHEPMC_NAME=hepmc-python-$PYHEPMC_VERSION
    PYHEPMC_URL=http://www.hepforge.org/archive/rivet/$PYHEPMC_NAME.tar.gz
    if test ! -e $PYHEPMC_NAME; then
        echo "Getting $PYHEPMC_URL"
        wget-untargz "$PYHEPMC_URL"
        rm -f hepmc-python
        ln -s $PYHEPMC_NAME hepmc-python || exit 2
    fi
fi


## AFS directory where LCG external packages are installed
LCGDIR=/afs/cern.ch/sw/lcg/external


## Choose names for env files and determine user's default shell
SHENV=rivetenv.sh
CSHENV=rivetenv.csh
USERSHENV=$SHENV
if test -n $(which finger &> /dev/null); then
    USERSH=$(finger $USER | grep Shell | sed -e 's/.*Shell:\ *\(.*\)/\1/')
    if $(echo "$USERSH" | grep -i "csh" &> /dev/null); then
        USERSHENV=$CSHENV
    fi
fi


## Get Boost
if [[ "$INSTALL_BOOST" == "yes" ]]; then
    echo "Installing a local copy of Boost"
    wget http://downloads.sourceforge.net/boost/boost_${BOOST_VERSION}_0.tar.gz?use_mirror=mesh -O- | tar xz
    cd boost_${BOOST_VERSION}_0
    echo "In $PWD"
    ./configure --prefix=$PREFIX
    make
    make install
    cd ..
    echo "In $PWD"
    cd $PREFIX/include
    echo "In $PWD"
    ln -s boost_${BOOST_VERSION}/boost boost
    cd ../..
    echo "In $PWD"
    BOOSTFLAGS=--with-boost=$PREFIX
    echo "Setting BOOSTFLAGS=$BOOSTFLAGS"
fi


## Are we able to use pre-built packages from CERN AFS?
if test -d "$LCGDIR" && test "$IGNORE_AFS" != "yes"; then
    echo "LCG AFS area available: using LCG packages"

    ## Platform tag: get distribution
    distribution=$(uname)
    if test -s "/etc/redhat-release"; then
        distribution="redhat"
        sltest=$(lsb_release -ds | grep "Scientific Linux")
        if test "$sltest"; then
            slc_major=$(lsb_release -rs | cut -f1 -d.)
            distribution="slc${slc_major}"
        fi
    fi

    ## Platform tag: get architecture
    machine32=$(uname -m | grep -E "i[3456]86") 
    machine64=$(uname -m | grep "x86_64")
    if test "$machine32"; then machine="ia32"; fi 
    if test "$machine64"; then machine="amd64"; fi

    ## Platform tag: get GCC version
    gcc_version=$(g++ --version | head -1 | cut -d" " -f3)
    gcc_major=$(echo $gcc_version | cut -d. -f1)
    gcc_minor=$(echo $gcc_version | cut -d. -f2)
    gcc_micro=$(echo $gcc_version | cut -d. -f30) 
    gcc_code="gcc${gcc_major}${gcc_minor}"

    LCGPLATFORM="${distribution}_${machine}_${gcc_code}"
    echo "Using LCG platform tag = $LCGPLATFORM"


    HEPMCPATH=$LCGDIR/HepMC/$HEPMC_VERSION/$LCGPLATFORM 
    echo "HepMC path: $HEPMCPATH"
    FASTJETPATH=$LCGDIR/fastjet/$FASTJET_VERSION/$LCGPLATFORM 
    echo "FastJet path: $FASTJETPATH"
    BOOST_VERSION=1.34.1
    BOOSTPATH=$LCGDIR/Boost/$BOOST_VERSION/$LCGPLATFORM
    BOOSTFLAGS=--with-boost-incpath=$BOOSTPATH/include/boost-${BOOST_VERSION//./_}
    echo "Compiling with: $BOOSTFLAGS"


    ## Python interface
    if test "$USE_PYTHON" == "yes"; then
        echo "Building hepmc-python"
        cd hepmc-python
        echo "In $PWD"
        ./configure --prefix=$PREFIX \
            --with-hepmc=$HEPMCPATH || exit 2
        make || exit 2
        make install || exit 2
        cd ..
        echo "In $PWD"
        echo
    fi


    ## Rivet
    echo "Building Rivet"
    cd rivet
    echo "In $PWD"
    ## Finally, run configure...
    ./configure --prefix=$PREFIX \
        --with-hepmc=$HEPMCPATH \
        --with-fastjet=$FASTJETPATH \
        $BOOSTFLAGS \
        $PYEXTFLAGS || exit 2
    make || exit 2
    make install || exit 2
    cd ..
    echo "In $PWD"

    ## Write sh env file
    > $SHENV
    echo "export PATH=$PREFIX/bin:\$PATH" >> $SHENV
    echo "export LD_LIBRARY_PATH=$PREFIX/lib:$HEPMCPATH/lib:$FASTJETPATH/lib:$CGALPATH/lib:\$LD_LIBRARY_PATH" >> $SHENV
    if test "$USE_PYTHON" == "yes"; then
        echo "export PYTHONPATH=\$PYTHONPATH:$pylibdir" >> $SHENV
    fi

    ## Write csh env file
    > $CSHENV
    echo "setenv PATH $PREFIX/bin:\$PATH" >> $CSHENV
    echo "setenv LD_LIBRARY_PATH $PREFIX/lib:$HEPMCPATH/lib:$FASTJETPATH/lib:$CGALPATH/lib:\$LD_LIBRARY_PATH" >> $CSHENV
    if test "$USE_PYTHON" == "yes"; then
        echo "setenv PYTHONPATH \$PYTHONPATH:$pylibdir" >> $CSHENV
    fi



else
    ## We don't have access to LCG AFS, so download the packages...

    ## Get HepMC
    HEPMCNAME=HepMC-$HEPMC_VERSION
    test -d $HEPMCNAME || wget-untargz http://lcgapp.cern.ch/project/simu/HepMC/download/$HEPMCNAME.tar.gz || exit 2
    conf-mk-mkinst $HEPMCNAME "--with-momentum=GEV --with-length=MM" || exit 2

    ## Get FastJet
    FASTJETNAME=fastjet-$FASTJET_VERSION
    test -d $FASTJETNAME || wget-untargz http://www.lpthe.jussieu.fr/~salam/repository/software/fastjet/$FASTJETNAME.tar.gz || exit 2
    if test "$FASTJETJADE" = "yes" -a -x "$(which autoreconf)"; then
        cd $FASTJETNAME
        if ! test -e "plugins/Jade"; then
            wget http://users.hepforge.org/~hoeth/fastjet/fastjet-2.3.4-jade.patch || exit 2
            patch -p1 < fastjet-2.3.4-jade.patch || exit 2
            autoreconf --install || exit 2
        fi;
        cd ..
    fi;
    conf-mk-mkinst $FASTJETNAME || exit 2


    ## Python interface
    if test "$USE_PYTHON" == "yes"; then
        #echo "Building hepmc-python"
        #cd hepmc-python
        #echo "In $PWD"
        #./configure --prefix=$PREFIX \
        #    --with-hepmc=$HEPMCPATH || exit 2
        #make || exit 2
        #make install || exit 2
        #cd ..
        #echo "In $PWD"
        #echo
        conf-mk-mkinst hepmc-python || exit 2
    fi


    ## Build and install Rivet
    test "$FASTJETJADE" = "yes" && RIVET_CONFIGURE_FLAGS="--enable-jade $PYEXTFLAGS"
    conf-mk-mkinst rivet $RIVET_CONFIGURE_FLAGS || exit 2

    ## Write sh env file
    > $SHENV
    echo "export PATH=$PREFIX/bin:\$PATH" >> $SHENV
    echo "export LD_LIBRARY_PATH=$PREFIX/lib:\$LD_LIBRARY_PATH" >> $SHENV
    if test "$USE_PYTHON" == "yes"; then
        echo "export PYTHONPATH=\$PYTHONPATH:$pylibdir" >> $SHENV
    fi
    if test -f $PREFIX/share/Rivet/rivet-completion; then
	echo "source $PREFIX/share/Rivet/rivet-completion" >> $SHENV
    fi

    ## Write csh env file
    > $CSHENV
    echo "setenv PATH $PREFIX/bin:\$PATH" >> $CSHENV
    echo "setenv LD_LIBRARY_PATH $PREFIX/lib:\$LD_LIBRARY_PATH" >> $CSHENV
    if test "$USE_PYTHON" == "yes"; then
        echo "setenv PYTHONPATH \$PYTHONPATH:$pylibdir" >> $CSHENV
    fi

fi


## Write environment variable information
echo
echo "All done. Now set some variables:"
cat $USERSHENV
echo "These variables are also written to $SHENV and $CSHENV, and"
echo "can be used in sh or csh shells respectively by sourcing, e.g."
echo ". $SHENV"
echo "or"
echo "source $CSHENV"
