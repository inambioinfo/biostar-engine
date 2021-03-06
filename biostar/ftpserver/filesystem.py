import logging
import time
import os

from pyftpdlib.filesystems import AbstractedFS
from django.contrib.auth.models import AnonymousUser
from biostar.engine.models import Data, Job, Access
from biostar.engine import auth
from biostar.accounts.models import Profile

from .util import parse_virtual_path, query_tab, index


logger = logging.getLogger("engine")
logger.setLevel(logging.INFO)


def fetch_file_info(fname, project, tab=None, tail=[], name=None):
    """
    Fetch the actual file path and filetype of a given instance.
    """

    # Get the Job or Data instance from the name and tab
    instance = query_tab(tab=tab, name=name or fname, show_instance=True, project=project)
    assert instance, "Does not exist"

    # Patch together the absolute path to the Job or Data file
    suffix = fname if not tail else os.path.join(*tail, fname)
    full_path = os.path.join(instance.get_data_dir(), suffix)

    # Return an actual filename with a type.
    rfname = full_path if name else instance.get_data_dir()
    filetype = 'dir' if (os.path.isdir(rfname)) else 'file'

    return rfname, filetype


def dir_list(base_dir, tail=[]):
    "Return contents of a given base dir ( and a tail)."
    try:
        # List sub-dirs found in /data and /results
        suffix = os.path.join(*tail)
        full_path = os.path.join(base_dir, suffix)
        return [os.path.basename(item.path) for item in os.scandir(full_path)]
    except Exception as exc:
        logger.error(f"{exc}")
        return []


class BiostarFileSystem(AbstractedFS):

    def __init__(self, root, cmd_channel, current_user=None):

        """
         - (str) root: the user "real" home directory (e.g. '/home/user')
         - (instance) cmd_channel: the FTPHandler class instance
         - (str) current_user: username of currently logged in user. Used to key user_table.
        """
        # Set initial current working directory.
        # By default initial cwd is set to "/" to emulate a chroot jail.
        # If a different behavior is desired (e.g. initial cwd = root,
        # to reflect the real filesystem) users overriding this class
        # are responsible to set _cwd attribute as necessary.

        self._cwd = root
        self._root = root
        self.cmd_channel = cmd_channel
        self.timefunc = time.localtime if cmd_channel.use_gmt_times else time.gmtime

        logger.info(f"current_user={current_user}")

        # Dict with all users stored by parent class
        self.user_table = self.cmd_channel.authorizer.user_table

        # Logged in user
        self.username = current_user
        self.user = self.user_table.get(current_user) or dict(user=AnonymousUser)

        # Projects the user has access to
        self.projects = auth.get_project_list(user=self.user["user"])

        # Data and results in project
        self.data = Data.objects.filter(project__in=self.projects, state__in=(Data.READY, Data.PENDING))

        self.jobs = Job.objects.filter(project__in=self.projects)

        # Get authorizer to set write permission on directories.
        self.authorizer = self.cmd_channel.authorizer

        super(BiostarFileSystem, self).__init__(root, cmd_channel)


    def ftp2fs(self, ftppath):
        """
        :param ftppath: relative virtual path requested by client
        :return:
        """
        abs_ftppath = super(BiostarFileSystem, self).ftp2fs(ftppath)

        logger.info(f"fs={abs_ftppath}, ftppath={ftppath}")

        root_project, tab, name, tail = parse_virtual_path(ftppath=abs_ftppath)

        if not name:
            logger.info(f"fs={abs_ftppath}, ftppath={ftppath}")
            # Only look at actual files, dir are returned as is
            return abs_ftppath

        assert tab in ('data', 'results'), tab
        instance = query_tab(tab=tab, name=name, show_instance=True, project=root_project)

        if not instance:
            # We let self.valid_path handle invalid paths
            return abs_ftppath

        try:
            fullname = os.path.join(instance.get_data_dir(), *tail)
            is_file = os.path.exists(fullname) and os.path.isfile(fullname)
            fname = fullname if is_file else abs_ftppath
        except Exception as exc:
            fname = abs_ftppath
            logger.error(f"{exc}")

        # Attempt to return a real file path, otherwise returns absolute ftppath.
        return fname


    def validpath(self, path):
        """
        Validates a virtual file path when dealing with directory traversal
        and also validates actual file paths when its time to download.

        :param path: current path requested by user
        :return: True if path is valid else False
        """

        logger.info(f"path={path}")

        # Check the user status.
        self._check_user_status()
        real_file, virtual_path = False, False

        # Check if its a virtual path first
        virtual_path = self.validate_virtual_path(path=path)

        # If it's not a virtual ftp path, then it has to be a real file path.
        if not virtual_path:
            real_file =  self.validate_actual_path(path=path)

        return real_file or virtual_path


    def isdir(self, path):

        root_project, tab, name, tail = parse_virtual_path(ftppath=path)
        is_dir = True

        # If the virtual path does not have a 'tail' then its a dir.
        if not tail or path == self.root:
            return is_dir
        try:
            if tail:
                path = os.path.join(query_tab(tab=tab, name=name, project=root_project), *tail)
                is_dir = not (os.path.exists(path) and os.path.isfile(path))
        except Exception as exc:
            logger.error(f"{exc}")

        logger.info(f"path={path}, is_dir={is_dir}")
        return is_dir


    def listdir(self, path):
        # This is the root as initialized in the base class

        logger.info(f"path={path}, cwd={self._cwd}, root={self.root}")

        root_project, tab, name, tail = parse_virtual_path(ftppath=path)

        # List projects when user is at the root
        if path == self.root:
            return [x.name for x in self.projects ]

        # Browse /data or /results inside of a project.
        if self.projects.filter(name=root_project) and not tab:
            return ['data', 'results']

        # List files in /data or /results
        is_tab = tab and (not name)
        if self.projects.filter(name=root_project) and is_tab:
            jobs = self.jobs.filter(project__name=root_project)
            queryset = self.data.filter(project__name=root_project) if tab == 'data' else jobs
            return [x.name for x in queryset ] or []

        # Take a look at specific instance in /data or /results
        is_instance = name and (not tail)
        base_dir = query_tab(tab=tab, name=name, project=root_project)
        # List the files inside of /data and /results tabs
        if base_dir and is_instance:

            return [os.path.basename(p.path) for p in os.scandir(base_dir)]

        # Dir list returned is different depending on the tab
        return dir_list(base_dir=base_dir, tail=tail)


    def chdir(self, path):
        """
        Change the current directory.
        """
        # note: process cwd will be reset by the caller

        logger.info(f"path={path}")
        #self._cwd = f"foo({path})
        self._cwd = self.fs2ftp(path)


    def format_mlsx(self, basedir, listing, perms, facts, ignore_err=True):
        logger.info(f"basedir={basedir} listing={listing} facts={facts} perms={perms}")

        lines = []
        root_project, tab, name, tail = parse_virtual_path(ftppath=basedir)

        is_project = root_project and (not tab)
        perm = self.set_permissions(basedir=basedir)

        for fname in listing:

            # Check if listing has multiple names
            # Let user know that both names point to same thing.
            if listing.count(fname) > 1:
                msg = f'"{fname}" occurs twice. Both point to the same location.'
                self.cmd_channel.respond(f'350  {msg}')

            if basedir == self.root or is_project:
                name = root_project if is_project else fname
                project = self.projects.filter(name=name).first()
                filetype, rfname = 'dir', project.get_project_dir()
            else:
                rfname, filetype = fetch_file_info(fname=fname, tab=tab,
                                                   name=name, tail=tail,
                                                   project=root_project)
            st = self.stat(rfname)
            unique = "%xg%x" % (st.st_dev, st.st_ino)
            modify = time.strftime("%Y%m%d%H%M%S", self.timefunc(st.st_mtime))

            lines.append(
                f"type={filetype};size={st.st_size};perm={perm};modify={modify};unique={unique}; {fname}")

        line = "\n".join(lines)
        yield line.encode('utf8', self.cmd_channel.unicode_errors)


    def _check_user_status(self):
        "Check if the logged in user is still valid. "
        user = self.user['user']
        if user.is_authenticated and user.profile.state in (Profile.BANNED, Profile.SUSPENDED):
            self.cmd_channel.respond(f"550  Your account has been {user.profile.get_state_display()}")
            self.cmd_channel.close()
            return False


    def validate_virtual_path(self, path):
        "Validate the ftp file path user has requested."

        root_project, tab, name, tail = parse_virtual_path(ftppath=path)

        # Check user did not leave /data or /results while in project.
        if tab and (tab not in ('data', 'results')):
            logger.info(f"is_valid={False}, tab not in data or resutls")
            return False

        if name and not self.projects.filter(name=root_project):
            logger.info(f"is_valid={False}, project does not exist")
            return False

        return True


    def validate_actual_path(self, path):
        "Make sure user has access to real path requested."

        valid_project_dirs = [p.get_project_dir() for p in self.projects]
        valid_job_dirs = [job.get_data_dir() for job in self.jobs]

        for basedir in valid_project_dirs + valid_job_dirs:
            if path.startswith(basedir):
                logger.info(f"path={path}, basedir={basedir}, is_valid={True and os.path.exists(path=path)}")
                return os.path.exists(path=path)

        logger.info(f"is_valid={False}")
        return False


    def access_to_perm(self, access):

        """
        Map biostar-engine access control to pyftpdlib's

        pyftplib permissions:
        Read permissions:
         - "e" = change directory (CWD command)
         - "l" = list files (LIST, NLST, STAT, MLSD, MLST, SIZE, MDTM commands)
         - "r" = retrieve file from the server (RETR command)
        Write permissions:
         - "a" = append data to an existing file (APPE command)
         - "d" = delete file or directory (DELE, RMD commands)
         - "f" = rename file or directory (RNFR, RNTO commands)
         - "m" = create directory (MKD command)
         - "w" = store a file to the server (STOR, STOU commands)
         - "M" = change file mode (SITE CHMOD command)
         - "T" = update file last modified time (MFMT command)

        """
        # Note: Nobody is allowed to delete for now.
        read_perms = "elr"
        write_perms = "wm"
        manager_perms = "f"

        perm_map = {
                    Access.NO_ACCESS: read_perms,
                    Access.READ_ACCESS: read_perms,
                    Access.WRITE_ACCESS: read_perms + write_perms,
                    }

        return perm_map.get(access, "el")


    def set_permissions(self, basedir):

        self._check_user_status()

        root_project, tab, name, tail = parse_virtual_path(ftppath=basedir)

        project = self.projects.filter(name=root_project).first()
        user = self.user["user"]

        access = None if not project else Access.objects.filter(user=user, project=project).first()
        access = access or Access(access=Access.NO_ACCESS)

        perm = self.access_to_perm(access=access.access)

        if basedir != self.root:
            # This is where the permissions are set
            self.authorizer.override_perm(username=self.username, directory=basedir, perm=perm)

        return perm