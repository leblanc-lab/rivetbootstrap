#! /usr/bin/env python

## $Date$
## $Revision$

__usage__ = """\
Download packages needed to get the Rivet system running, in several 
different permutations.

TODO:
 * Build logging: stream as it builds, like 'tee'?
 * Control over num of 'make' threads
"""

import os, sys, logging, shutil
from optparse import OptionParser

DEFAULTPREFIX = os.path.join(os.getcwd(), "local")

parser = OptionParser(usage=__usage__)
parser.add_option("--prefix", metavar="INSTALLDIR", default=DEFAULTPREFIX, dest="PREFIX", 
                  help="Location to install packages to (default = %default)")
parser.add_option("--force", action="store_true", default=False, dest="FORCE", 
                  help="Overwrite existing tarballs")
parser.add_option("--devmode", action="store_true", default=False, dest="DEV_MODE", 
                  help="Use the SVN development head version of Rivet")
parser.add_option("--lcgextdir", default="/afs/cern.ch/sw/lcg/external", dest="LCGDIR", 
                  help="Standard location of LCG external packages")
parser.add_option("--ignore-lcgext", action="store_true", default=False, dest="IGNORE_LCG", 
                  help="Always bootstrap from sources, even if LCG versions are available")
parser.add_option("--rivet-version", default="1.1.3b0", dest="RIVET_VERSION", 
                  help="Explicitly specify version of Rivet to get and use")
parser.add_option("--hepmc-version", default="2.04.01", dest="HEPMC_VERSION", 
                  help="Explicitly specify version of HepMC to get and use")
parser.add_option("--hepmc-url", default="http://lcgapp.cern.ch/project/simu/HepMC/download/", 
                  dest="HEPMC_URL", help="Base URL for HepMC tarball downloads")
parser.add_option("--fastjet-version", default="2.4.1", dest="FASTJET_VERSION", 
                  help="Explicitly specify version of FastJet to get and use")
parser.add_option("--fastjet-url", default="http://www.lpthe.jussieu.fr/~salam/repository/software/fastjet/", 
                  dest="FASTJET_URL", help="Base URL for FastJet tarball downloads")
parser.add_option("--boost", metavar="DIR", default=None, dest="BOOST_DIR", 
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


## Build location
ROOT = os.path.abspath(os.getcwd())


## Build location
DLDIR = os.path.abspath(os.path.join(ROOT, "downloads"))
if not os.path.exists(DLDIR):
    os.makedirs(DLDIR)
if not os.access(DLDIR, os.W_OK):
    logging.error("Can't write to downloads directory, %s... exiting" % DLDIR)

## Build location
BUILDDIR = os.path.abspath(os.path.join(ROOT, "build"))
if not os.path.exists(BUILDDIR):
    os.makedirs(BUILDDIR)
if not os.access(BUILDDIR, os.W_OK):
    logging.error("Can't write to build directory, %s... exiting" % BUILDDIR)

## Install to the PREFIX location
PREFIX = os.path.abspath(opts.PREFIX)
if not os.path.exists(PREFIX):
    os.makedirs(PREFIX)
if not os.access(PREFIX, os.W_OK):
    logging.error("Can't write to installation directory, %s... exiting" % PREFIX)


###########################


## Function to grab a tarball from the Web
def get_tarball(url, outname=None):
    if not outname:
        import urlparse
        outname = os.path.basename(urlparse.urlparse(url)[2])
    outpath = os.path.join(DLDIR, outname)
    if os.path.exists(outpath):
        if not opts.FORCE:
            logging.info("Not overwriting tarball at %s" % outpath)
            return outpath
        else:
            logging.info("Overwriting tarball at %s" % outpath)
            os.remove(outpath)
    import urllib2
    hreq = None
    out = None
    try:
        logging.info("Downloading %s" % url)
        hreq = urllib2.urlopen(url)
        out = open(outpath, "w")
        out.write(hreq.read())
        out.close()
        hreq.close()
        return outpath
    except urllib2.URLError:
        logging.error("Problem downloading PDF set from '%s'" % url)
        if hreq:
            hreq.close()
    except IOError:
        logging.error("Problem while writing PDF set to '%s'" % outpath)
        if out:
            out.close()
        if hreq:
            hreq.close()
    return None


## Function to unpack a tarball
def unpack_tarball(path):
    import tarfile
    tar = tarfile.open(path)
    #tar.extractall()
    for i in tar.getnames():
        tar.extract(i, path=BUILDDIR)
    tar.close()


## Convenience function to get and unpack the tarball
def get_unpack_tarball(tarurl, outname=None):
    outfile = get_tarball(tarurl, outname)
    unpack_tarball(outfile)


## Function to enter an expanded tarball and run the usual
## autotools ./configure, make, make install mantra
def conf_mk_mkinst(d, extraopts=""):
    prevdir = os.getcwd()
    if os.access(d, os.W_OK):
        os.chdir(d)
        confcmd = "./configure --prefix=%s %s" % (PREFIX, extraopts)
        logging.info("Building in %s: %s" % (os.getcwd(), confcmd))
        import commands #< TODO: replace this with 'subprocess' when Py 2.4 is guaranteed
        st, op = commands.getstatusoutput(confcmd)
        if st == 0:
            st, op = commands.getstatusoutput("make -j2 && make -j2 install")
        if st != 0:
            logging.error(op)
            sys.exit(1)
        os.chdir(prevdir)
    else:
        logging.error("Couldn't find $1... exiting")
        sys.exit(1)


##############################


## Get Rivet source either from released tarballs or SVN

## USER MODE
## Get Rivet tarball (for non-developers)
if not opts.DEV_MODE:
    RIVET_NAME = "Rivet-" + opts.RIVET_VERSION
    RIVET_URL = "http://www.hepforge.org/archive/rivet/%s.tar.gz" % RIVET_NAME
    logging.info("Getting %s" % RIVET_URL)
    get_unpack_tarball(RIVET_URL)
    os.chdir(BUILDDIR)
    if not os.path.exists("rivet"):
        os.symlink(RIVET_NAME, "rivet")
    elif not os.path.islink("rivet"):
        logging.warn("A 'rivet' directory already exists in %s, but is not a symlink to an expanded tarball" % BUILDDIR)
        sys.exit(1)


## DEVELOPER MODE
## If we've got SVN and there is no already-checked out version
## of Rivet in this directory, then check out/update
## the SVN head versions using the HTTP access method
else:
    path = []
    if os.environ.has_key("PATH"):
        path += os.environ["PATH"]
    if os.environ.has_key("path"):
        path += os.environ["path"]
    for pkg in ["svn", "autoconf", "autoreconf", "automake", "libtool"]:
        found = False
        for d in path:
            if os.access(os.path.join(d, pkg), os.X_OK):
                found = True
                break
        if not found:
            logging.error("You must have %s installed to bootstrap in developer mode" % pkg)
            sys.exit(1)

    os.chdir(BUILDDIR)
    if not os.path.exists("rivet"):
        st, op = commands.getstatusoutput("svn co http://svn.hepforge.org/rivet/trunk rivet")
    os.chdir("rivet")
    st, op = commands.getstatusoutput("svn update")
    if not os.path.exists("configure"):
        st, op = commands.getstatusoutput("autoreconf -i")
        if st != 0:
            sys.exit(2)
    os.chdir(BUILDDIR)


## Get Boost
BOOSTFLAGS = None
if opts.INSTALL_BOOST:
    logging.info("Installing a local copy of Boost")
    boostname = "boost_%s" % opts.BOOST_VERSION
    boosttarname = boostname + ".tar.gz"
    boosturl = "http://downloads.sourceforge.net/boost/%s?use_mirror=mesh" % boosttarname
    boostincdir_outer = os.path.join(PREFIX, "include", "boost-%s" % opts.BOOST_VERSION[:-2])
    if not os.path.exists(boostincdir_outer):

        conf_mk_mkinst(boostbuilddir)
    ## Fix up the crappy default Boost install structure
    boostincdir = os.path.join(PREFIX, "include", "boost")
    boostincdir_inner = os.path.join(boostincdir_outer, "boost")
    if not os.path.exists(boostincdir):
        if os.path.exists(boostincdir_inner):
            logging.info("Symlinking Boost include dir: %s -> boost" % boostincdir_inner)
            os.symlink(boostincdir_inner, boostincdir)
        else:
            logging.error("Can't work out how to make a standard Boost include dir")
            sys.exit(2)
    logging.debug("Setting BOOST_DIR = " + PREFIX)
    opts.BOOST_DIR = PREFIX


## Are we able to use pre-built packages from CERN AFS?
if not opts.IGNORE_LCG and os.path.isdir(opts.LCGDIR):
    logging.info("LCG area available: using LCG-built packages")

    ## Platform tag: get distribution
    distribution = commands.getoutput("uname")
    if os.path.exists("/etc/redhat-release"):
        distribution = "redhat"
        sltest = commands.getoutput("lsb_release -ds")
        if "Scientific Linux" in sltest:
            version = commands.getoutput("lsb_release -rs").split(".")
            distribution = "slc" + version[0]

    ## Platform tag: get architecture
    uname_m = commands.getoutput("uname -m")
    machine = "ia32"
    if "64" in uname_m:
        machine = "amd64"

    ## Platform tag: get GCC version
    gcc_version = commands.getoutput('g++ --version | head -1 | cut -d" " -f3').split(".")
    gcc_major = gcc_version[0]
    gcc_minor = gcc_version[1]
    gcc_micro = gcc_version[2]
    gcc_code = "gcc%s%s" % (gcc_major, gcc_minor)
    ## Historical exceptions
    if gcc_code in ["gcc32", "gcc40"]:
      gcc_code += gcc_micro
    fi

    LCGPLATFORM = "%s_%s_%s" % (distribution, machine, gcc_code)
    logging.info("Using LCG platform tag = " + LCGPLATFORM)


    ## Now work out paths to give to Rivet
    HEPMCPATH = os.path.join(opts.LCGDIR, "HepMC", opts.HEPMC_VERSION, LCGPLATFORM)
    FASTJETPATH = os.path.join(opts.LCGDIR, "fastjet", opts.FASTJET_VERSION, LCGPLATFORM)
    if not opts.INSTALL_BOOST:
        lcg_boost_version = "1.34.1"
        opts.BOOST_DIR = os.path.join(opts.LCGDIR, "Boost", lcg_boost_version, LCGPLATFORM)
        ## This wouldn't be needed if Boost followed normal installation conventions...
        BOOSTFLAGS = "--with-boost-incpath=%s/include/boost-%s" % (opts.BOOST_DIR, lcg_boost_version.replace(".", "_"))

else:
    ## We don't have access to LCG AFS, or are ignoring it, so we download the packages...

    ## Get and build HepMC
    hepmcname = "HepMC-" + opts.HEPMC_VERSION
    os.chdir(BUILDDIR)
    if not os.path.exists(hepmcname):
        hepmctarname = hepmcname + ".tar.gz"
        hepmcurl = os.path.join(opts.HEPMC_URL, hepmctarname)
        get_unpack_tarball(hepmcurl)
        conf_mk_mkinst(os.path.join(BUILDDIR, hepmcname), "--with-momentum=GEV --with-length=MM")
    HEPMCPATH = PREFIX

    ## Get and build FastJet
    fastjetname = "fastjet-" + opts.FASTJET_VERSION
    os.chdir(BUILDDIR)
    if not os.path.exists(fastjetname):
        fastjettarname = fastjetname + ".tar.gz"
        fastjeturl = os.path.join(opts.FASTJET_URL, fastjettarname)
        get_unpack_tarball(fastjeturl)
        conf_mk_mkinst(os.path.join(BUILDDIR, fastjetname), "--enable-shared --enable-allcxxplugins")
    FASTJETPATH = PREFIX


## TODO: AGILe


## Build and install Rivet
RIVET_CONFIGURE_FLAGS = ""
logging.debug("HepMC path: " + HEPMCPATH)
RIVET_CONFIGURE_FLAGS += " --with-hepmc=%s" % HEPMCPATH
logging.debug("FastJet path: " + FASTJETPATH)
RIVET_CONFIGURE_FLAGS += " --with-fastjet=%s" % FASTJETPATH
if opts.BOOST_DIR:
    logging.debug("Boost path: " + opts.BOOST_DIR)
    RIVET_CONFIGURE_FLAGS += " --with-boost=%s" % opts.BOOST_DIR
## Nasty hack in case the Boost headers are installed some rubbish way:
if BOOSTFLAGS:
    logging.debug("Boost flags: " + BOOSTFLAGS)
    RIVET_CONFIGURE_FLAGS += " " + BOOSTFLAGS
## Energise!
conf_mk_mkinst(os.path.join(BUILDDIR, "rivet"), RIVET_CONFIGURE_FLAGS)


## Collect and write out environment variables
env = {}

## Path env
env["PATH"] = ":".join([os.path.join(PREFIX, "bin"), "$PATH"])

## Lib env
libdirs = []
for d in [PREFIX, HEPMCPATH, FASTJETPATH]: # CGALPATH
    libdir = os.path.join(d, "lib")
    if libdir not in libdirs:
        libdirs.append(libdir)
env["LD_LIBRARY_PATH"] = ":".join(libdirs + ["$LD_LIBRARY_PATH"])

## Python env
pyversion = "%d.%d" % (sys.version_info[0], sys.version_info[1])
pylibdirs = []
for ld in ["lib", "lib64" "lib32"]:
    pylibdir = os.path.join(PREFIX, ld, "python%s/site-packages" % pyversion)
    if os.path.exists(pylibdir):
        pylibdirs.append(pylibdir)
env["PYTHONPATH"] = ":".join(pylibdirs + ["$PYTHONPATH"])


## Write out env files

## sh
SHENV = ""
for k, v in env.iteritems():
    SHENV += "export %s=%s\n" % (k,v)
comppath = os.path.join(PREFIX, "share", "Rivet", "rivet-completion")
if os.path.exists(comppath):
    SHENV += ". %s\n" % comppath
os.chdir(ROOT)
f = open("rivetenv.sh", "w")
f.write(SHENV)
f.close()

## csh
CSHENV = "" 
for k, v in env.iteritems():
    CSHENV += "setenv %s %s\n" % (k,v)
os.chdir(ROOT)
f = open("rivetenv.csh", "w")
f.write(CSHENV)
f.close()

## Tell the user
print
logging.info("All done. Now set some variables in your shell:")
logging.info("In sh shell:\n" + SHENV)
logging.info("In csh shell:\n" + CSHENV)
logging.info("These can be used by sourcing, e.g.\n. rivetenv.sh\nor\nsource rivetenv.csh")
