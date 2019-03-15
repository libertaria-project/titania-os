#!/usr/bin/env python3
try:
    from fuse import FUSE, FuseOSError, Operations
# For testing on Ubuntu
except ModuleNotFoundError:
    from fusepy import FUSE, FuseOSError, Operations

import errno
import json
import os
import re
import stat
import subprocess
import sys
import time
import threading


class PydAppHubFuse(Operations):
    """
    Don't try to prononce the name of the class
    I'm not liable for the daemons you might 
    summon if you do.
    """

    def __init__(self, jsonroot, systemdroot, dataroot):
        self.jsonroot = jsonroot
        self.systemdroot = systemdroot
        self.dataroot = dataroot

        # Config file cache
        self.cache = {}

        # Ensuring after open() the result doesn't change
        self.filecache = {}
        # TODO: rely on the set of keys of above instead
        self.lastfd = -1

        # dApp database collected from JSONs 
        # TODO error if file not found etc
        with open(jsonroot) as fp:
            jsonobj = json.load(fp)

        self.dapps = { v['id']:v for v in jsonobj }

    def __classify(self, path):
        """
        Classifies the incoming path value:
         - None = invalid path
         - True = valid directory
         - dapp name = valid dapp.conf, corresponding entry is returned
        """

        # Root is a valid directory
        if path == '/':
            return True
        
        # Check if the directory corresponds to dapp pattern
        # TODO: what are valid dapp names and how they are named anyway?
        m = re.match("^/dapp@([A-Za-z-_.]+).service.d(/.*)?$", path)
        if not m:
            return None
        dapp = m.group(1)

        # Check if we are dealing with a directory
        fname = m.group(2)
        if not fname:
            return True

        # Check if we have that dapp
        if dapp not in self.dapps:
            return None

        # Find the entry if the filename is correct
        if fname == '/dapp.conf' or fname == '/dapp.env':
            return dapp 

        return None

    def __getobj(self, path):
        """
        Same as __classify but automatically raises ENOENT
        """
        obj = self.__classify(path)

        # Cut what's not ours
        if not obj:
            raise FuseOSError(errno.ENOENT)

        return obj

    def __genenv(self, dapp):
        """
        Generates an environment file for a given dapp
        """
        d = self.dapps[dapp]

        env = '''#
# Automatically generated by FUSE from dApp Hub JSON
# Do not [attempt] to edit
#
'''
        
        # TODO: escape quotes if necessary (probably not)
        env += '\n'.join("{}={}".format(v['name'],v['value']) for v in d['env'] if v['value'])
        env += '\n'

        return env

    def __genconfig(self, dapp):
        """
        Generates and return drop-in config data for a given dapp
        """

        d = self.dapps[dapp]

        conf = '''#
# Automatically generated by FUSE from dApp Hub JSON
# Do not [attempt] to edit
#
[Unit]
Description={}

[Service]
'''.format(d['name'])

        # Function to build a -p option
        def gen_port_spec(pobject):
            dapp_port = pobject.get('dapp_port', pobject['port'])
            return '-p{}:{}/{}'.format(pobject['port'], dapp_port, pobject['protocol']) 

        # Port publishing setup
        if 'ports' in d and d['ports']:
            conf += 'Environment="DAPP_DOCKER_PORTS=%s"' % ' '.join(gen_port_spec(port) for port in d['ports'] if port['type'] != 'internal')

        # Volumes
        # TODO: attack surface: paths containing spaces/quotes etc
        # TODO: check that path is absolute
        conf += '\n'
        if 'volumes' in d and len(d['volumes']) > 0:
            conf += 'Environment="DAPP_DOCKER_VOLUMES=%s"' % ' '.join('-v {0}/{1}{2}:{2}'.format(self.dataroot, d['id'], v) for v in d['volumes'])

        # Environment setup, passing the file instead of fragile shell string
        # TODO: formalise which variables get automatically set (LAT/LON etc) for the container
        # TODO: check how docker handles escaping and shell expansions
        conf += '\n'
        conf += 'Environment=DAPP_DOCKER_ENV=--env-file={}/dapp@{}.service.d/dapp.env'.format(self.systemdroot,d['id'])

        # Providing image name and filename for dapp@.service to use
        conf += '\n# Making sure we overwrite previous values\n'
        conf += 'Environment=DAPP_DOCKER_IMAGE=%s\n' % d['image']

        # TODO: consider removal
        # Being explicit here so that we don't have to wrap in a shell script
        # conf += 'Environment=DAPP_DOCKER_IMAGE_FILE=/var/lib/docker/preinstall/%s.tar\n' % d['image'].replace('/','_').replace(':','_')         
        # conf += '\n'

        # If we have static assets, provide an environment variable
        if 'staticpath' in d:
            conf += 'Environment="DAPP_STATIC_PATH=%s"' % d['staticpath']

        # TODO: remove this ASAP after dapps realize they can chown stuff on their own
        # TODO: exploitable with shell injection
        # Currently it's a terrible design

        if 'volumes' in d and len(d['volumes']) > 0:
            conf += 'Environment="DAPP_CHOWN_PATHS=%s"' % ' '.join('{}/{}{}'.format(self.dataroot, d['id'], v) for v in d['volumes'])
            conf += '\n'

        if 'volumechown' in d:
            conf += 'Environment=DAPP_CHOWN_UID=%s' % d['volumechown']
            conf += '\n'

        return conf

    def __getfile(self, dapp, ext):
        """
        Returns config data for a given dapp with lazy generation and cache/
        """

        # Check cache
        key = dapp + ext
        if key not in self.cache:
            # Pick up the respective generator
            gen_f = self.__genconfig if ext == '.conf' else self.__genenv

            self.cache[key] = gen_f(dapp)
        # Okay we need to generate
        return self.cache[key]

    def access(self, path, mode):
        obj = self.__getobj(path)

        # Allow read/execute on / and valid dirs
        # read only on anything else
        isdir = type(obj) is not str
        if (mode & os.W_OK) or (not isdir and mode & os.X_OK):
            raise FuseOSError(errno.EACCES)

    # TODO: support reading by handle?

    def getattr(self, path, fh):
        obj = self.__getobj(path)
        isdir = type(obj) is not str
        ext = path[path.rfind('.'):]

        # TODO: meaningful values
        st_mode = (stat.S_IFDIR | 0o755) if isdir else (stat.S_IFREG | 0o644)
        st_size = 0 if isdir else len(self.__getfile(obj, ext))
        res = { 
            'st_atime': 0,
            'st_ctime': 0,
            'st_gid':   0,  
            'st_mode':  st_mode,
            'st_mtime': 0,
            'st_nlink': 0,
            'st_size':  st_size,
            'st_uid':   0
        }

        return res

    def readdir(self, path, fh):
        obj = self.__getobj(path)
        # Can't list files
        if type(obj) is dict:
            raise FuseOSError(errno.EBADF)
        dirents = ['.', '..']
        # Root lists valid units
        if path == '/':
            dirents.extend('dapp@%s.service.d' % dapp for dapp in self.dapps)
        # Else only one file
        else:
            dirents.append('dapp.conf')
            dirents.append('dapp.env')

        # Sufficiently recent python required
        yield from dirents

    # TODO: statfs
    # TODO: what if path doesn't mach definition?
    def open(self, path, flags):
        obj = self.__getobj(path)
        # Determine extension
        ext = path[path.rfind('.'):]

        # if type(obj) is not str: TODO then what???
        # TODO: not multithreading friendly
        self.lastfd += 1
        self.filecache[self.lastfd] = self.__getfile(obj, ext)
        return self.lastfd

    # TODO: here and below invalid descriptor error
    def release(self, path, fh):
        del self.filecache[self.lastfd]

    def read(self, path, length, offset, fh):
        doc = self.filecache[fh]
        end = offset + min(len(doc) - offset, length)
        return doc[offset:end].encode('ascii')

    # Silently nod when asked to sync instead of ENOSYS error
    def fsync(self, *args, **kwargs):
        pass


# Standalone operation
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: ./dapp-sytemd-bridge.py /path/to/json /mount/point /datafs/path")
        sys.exit(1)

    driver = PydAppHubFuse(sys.argv[1], sys.argv[2], sys.argv[3])
    # Uncomment for debugging
    #indent = 0
    #for m in dir(driver):
    #    fun = getattr(driver,m) 
    #    if m[0]!='_' and type(fun) is type(driver.fsync):
    #        def trace_method(fun, name):
    #            def f(*args, **kwargs):
    #                global indent
    #                print("{}[TRACE]: {}({},{}) ".format('\t'*indent, name, args, kwargs))
    #                indent += 1
    #                try:
    #                    res = fun(*args, **kwargs)
    #                except:
    #                    indent -= 1
    #                    print("{}exception".format('\t'*indent))
    #                    raise
    #                indent -= 1
    #                print("{}return {}".format('\t'*indent,res))
    #                return res
    #            return f
    #        setattr(driver, m, trace_method(fun, m))

    def notify_systemd():
        while True:
            time.sleep(0.1)
            returncode = subprocess.Popen(['mountpoint', sys.argv[2]]).wait()
            if returncode == 0:
                subprocess.run(['systemctl', 'daemon-reload'])
                subprocess.run(['systemd-notify', 'READY=1'])
                break
        print('dapp systemd bridge is up')

    t = threading.Thread(target=notify_systemd, daemon=True)
    t.start()

    FUSE(driver, sys.argv[2], nothreads=True, foreground=True, allow_other=True)

    t.join()

