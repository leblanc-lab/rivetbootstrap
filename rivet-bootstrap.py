#! /usr/bin/env python

## $Date$
## $Revision$

__usage__ = """\
Download packages needed to get the Rivet system running, in several 
different permutations.

TODO: 

 * Make it possible to run without internet access if expanded tarballs 
   are already in place.
"""

import os, sys, logging, shutil
from optparse import OptionParser

DEFAULTPREFIX = os.path.join(os.cwd(), "local")

parser = OptionParser(usage=__usage__)
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
    logging.error("Can't write to installation directory, %s... exiting" % PREFIX)


# ## Set up Python install area
# logging.verbose("Setting up Python library install area: must exist and be in $PYTHONPATH")
# pyversion =  "%d.%d" % (sys.version_info[0], sys.version_info[1])
# pylibdir = os.path.join(PREFIX, "lib", "python%s/site-packages" % pyversion)



## Function to grab a tarball from the Web
def get_tarball(url):
    if not os.path.exists("downloads"):
        logging.debug("Making downloads dir")
        os.mkdir("downloads")
    import urlparse
    basename = os.path.basename(urlparse.urlparse(url).path)
    outpath = os.path.join("downloads", basename)
    import urllib2
    try:
        hreq = urllib2.urlopen(url)
        out = open(outpath, "w")
        out.write(hreq.read())
        out.close()
        hreq.close()
        return outpath
    except urllib2.URLError:
        logging.error("Problem downloading PDF set from '%s'" % url)
        hreq.close()
    except IOError:
        logging.error("Problem while writing PDF set to '%s'" % outpath)
        out.close()
        hreq.close()
    return None


## Function to unpack a tarball
def unpack_tarball(path):
    import tarfile
    tar = tarfile.open(path)
    tar.extractall()
    tar.close()


## Convenience function to get and unpack the tarball
def get_unpack_tarball(tarurl):
    ## TODO: run in 'build' directory?
    outfile = get_tarball(tarurl)
    unpack_tarball(outfile)


## Function to enter an expanded tarball and run the usual
## autotools ./configure, make, make install mantra
def conf_mk_mkinst(d, extraopts=""):
    if os.access(os.W_OK, d):
        os.setcwd(d)
        confcmd = "./configure --prefix=%s --enable-shared %s" % (PREFIX, extraopts)
        logging.info(confcmd)
        import commands #< TODO: replace this with 'subprocess' when Py 2.4 is guaranteed
        st, op = commands.getstatusoutput(confcmd)
        if st == 0:
            st, op = commands.getstatusoutput("make && make install")
        if st != 0:
            sys.exit(1)
    else:
        logging.error("Couldn't find $1... exiting")
        sys.exit(1)


##############################


## Get Rivet either from released tarballs or SVN
if not opts.DEV_MODE:
    ## USER MODE
    ## Get Rivet tarball (for non-developers)
    RIVET_NAME = "Rivet-" + opts.RIVET_VERSION
    RIVET_URL = "http://www.hepforge.org/archive/rivet/%s.tar.gz" % RIVET_NAME
    logging.info("Getting %s" % RIVET_URL)
    get_unpack_tarball(RIVET_URL)
    os.symlink(RIVET_NAME, "rivet")

else:
    ## DEVELOPER MODE
    ## If we've got SVN and there is no already-checked out version
    ## of Rivet in this directory, then check out/update
    ## the SVN head versions using the HTTP access method
    path = os.environ["PATH"]
    for pkg in ["svn", "autoconf", "autoreconf", "automake", "libtool"]:
        found = False
        for d in path:
            if os.access(os.X_OK, os.path.join(d, pkg)):
                found = True
                break
        if not found:
            logging.error("You must have %s installed to bootstrap in developer mode" % pkg)
            sys.exit(1)

    if not os.path.exists("rivet"):
        st, op = commands.getstatusoutput("svn co http://svn.hepforge.org/rivet/trunk rivet")
    os.chdir("rivet")
    st, op = commands.getstatusoutput("svn update")
    if not os.path.exists("configure"):
        st, op = commands.getstatusoutput("autoreconf -i")
        if st != 0:
            sys.exit(2)
    os.chdir(BUILDROOT)


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
