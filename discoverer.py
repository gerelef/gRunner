import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional, Literal, Generator

import desktop_entry_lib as dtl
from loguru import logger

import db
from globals import Global, autostr, timeit, Configuration


@autostr
class ExecutableFile:

    def __init__(self, directory: str, fname: str):
        self.dir = directory
        self.fname = fname
        self.path = Path(self.dir, self.fname)
        self.is_on_path = str(self.dir) in Global.PATH_VALUES

    def get_path(self):
        return self.path

    def is_bin_in_path(self):
        return self.is_on_path


@autostr
class Application(ABC):

    def __init__(self, opened_count: int = 0, last_opened_utc: float = .0, first_opened_utc: float = .0):
        self.opened_count = opened_count
        self.last_opened_utc = last_opened_utc
        self.first_opened_utc = first_opened_utc

    def update_opened_count_meta(self, count: int):
        self.opened_count = count

    def update_last_opened_utc_meta(self, last_opened: float):
        self.last_opened_utc = last_opened

    def update_first_opened_utc_meta(self, first_opened: float):
        self.first_opened_utc = first_opened

    @abstractmethod
    def get_application_type(self) -> Literal["binary", "dotdesktop", "flatpak", "snap"]:
        pass

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_full_path(self):
        pass

    @abstractmethod
    def get_readable_path(self):
        pass

    @abstractmethod
    def get_icon(self):
        pass

    @abstractmethod
    def run(self, args: list[str] = ""):
        pass

    def convert_path_to_readable(self, s: str):
        p = s.replace(str(Path.home()), "~")
        if len(p) > 30 and len((pp := p.split(os.sep))) > 5:
            return f"{pp[0]}{os.sep}{pp[1]}{os.sep}{pp[2]}{os.sep}...{os.sep}{pp[-2]}{os.sep}{pp[-1]}{os.sep}"
        return p


# TODO complete implementation
# TODO implement db saving https://www.tutorialspoint.com/peewee/peewee_update_existing_records.htm
# TODO implement dbus
# TODO find a way to support snap packages
@autostr
class XDGDesktopApplication(Application):

    def __init__(self,
                 dotdesktop_fp: Path | str,
                 df_name: str,
                 df_exec: Optional[str],
                 df_icon: Optional[str],
                 opened_count: int = 0,
                 last_opened_utc: float = None,
                 first_opened_utc: float = None
                 ):
        super().__init__(opened_count=opened_count, last_opened_utc=last_opened_utc, first_opened_utc=first_opened_utc)
        self.dfp: str = str(dotdesktop_fp)
        self.name: str = df_name
        self.exec: str = df_exec
        self.icon: str = df_icon

        self.sanitized_exec = self.exec.split(" ")

    def is_bin_path_exec(self):
        return os.sep not in self.sanitized_exec[0]

    def get_application_type(self):
        if "flatpak" in self.sanitized_exec[0]:
            return "flatpak"

        return "dotdesktop"

    def get_icon(self):
        pass

    def get_name(self):
        return self.name

    def get_full_path(self) -> str:
        return self.sanitized_exec[0]

    def get_readable_path(self):
        return self.convert_path_to_readable(self.sanitized_exec[0])

    def get_full_path_dfp(self):
        return self.dfp

    def get_readable_path_dfp(self):
        return self.convert_path_to_readable(self.dfp)

    def run(self, args: list[str] = ""):
        pass


# TODO implement db saving https://www.tutorialspoint.com/peewee/peewee_update_existing_records.htm
@autostr
class PlainApplication(Application):

    def __init__(self,
                 bin_path: str,
                 opened_count: int = 0,
                 last_opened_utc: float = None,
                 first_opened_utc: float = None):
        super().__init__(opened_count=opened_count, last_opened_utc=last_opened_utc, first_opened_utc=first_opened_utc)
        self.path = bin_path
        self.name = str(self.path).split(os.sep)[-1]

    def get_application_type(self) -> Literal["binary", "dotdesktop", "flatpak", "snap"]:
        return "binary"

    def get_name(self):
        return self.name

    def get_icon(self):
        return "application-x-executable-symbolic"

    def get_full_path(self):
        return self.path

    def get_readable_path(self):
        return self.convert_path_to_readable(self.path)

    def run(self, args: list[str] = ""):
        pass


@autostr
class FSExecutableFinder:
    # noinspection PyTypeChecker
    def __init__(self, cfg: Configuration):
        self.recursive: bool = cfg.get_recursive()
        self.paths: list[str] = cfg.get_paths()

    def _convert_executable_to_application(self, ap: ExecutableFile):
        return PlainApplication(ap.path)

    def _convert_dotdesktop_to_application(self, dp: Path) -> Optional[Application]:
        df = dtl.DesktopEntry.from_file(dp)
        if df.Type == "Application" and df.should_show():
            return XDGDesktopApplication(dp, df.Name.get_translated_text(), df.Exec, df.Icon)
        return None

    # noinspection PyTypeChecker
    def _join_application_entries(self,
                                  executables: list[ExecutableFile],
                                  dotdesktops: list[ExecutableFile]) -> dict[str, Application]:
        # https://specifications.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html)
        # Note:
        # according to the freedesktop spec
        # the "Exec=" key is not required, if DBusActivatable is set to true; however I've found that (on my system)
        # any desktop entry, that's an "Application" & set to be shown, even if the DBusActivatable is set to true,
        # they will have a valid "Exec=" key for "compatibility reasons", as the spec suggests.
        # This, ofcourse, favours us. However, in the future, when all critical issues & other bugs have been fixed,
        # means we should definitely take a look into this.
        binary_applications: dict[str, PlainApplication] = {}
        dotdesktop_applications: dict[str, XDGDesktopApplication] = {}
        for d in dotdesktops:
            if (dp := d.get_path()).exists():
                if app := self._convert_dotdesktop_to_application(dp):
                    dotdesktop_applications[str(dp)] = app

        self._filter_xdg_from_binary_entries(executables, dotdesktop_applications.values())

        for a in executables:
            if (dp := a.get_path()).exists():
                binary_applications[str(dp)] = self._convert_executable_to_application(a)

        return binary_applications | dotdesktop_applications

    def _filter_xdg_from_binary_entries(self,
                                        executable: list[ExecutableFile],
                                        xdg_applications: list[XDGDesktopApplication]):
        common_bins: list[ExecutableFile] = []
        for xdg in xdg_applications:
            for binary in executable:
                if xdg.get_full_path() == binary.fname and binary.is_on_path \
                        or xdg.get_full_path() == str(binary.get_path()):
                    if binary not in common_bins:
                        common_bins.append(binary)
                    break

        for binary in common_bins:
            executable.remove(binary)

    def _walk_path(self, path: Path) -> tuple[list[ExecutableFile], list[ExecutableFile]]:
        executable: list[ExecutableFile] = []
        dotdesktop: list[ExecutableFile] = []

        for current_path, _, files in os.walk(path):
            for file in files:
                if file.endswith(".desktop"):
                    dotdesktop.append(ExecutableFile(current_path, file))
                    continue

                fp = Path(current_path, file)
                if os.access(fp, os.X_OK):
                    executable.append(ExecutableFile(current_path, file))

            if not self.recursive:
                break

        return executable, dotdesktop

    @timeit
    def walk(self) -> dict[str, Application]:
        executables: list[ExecutableFile] = []
        dotdesktops: list[ExecutableFile] = []

        for p in self.paths:
            path = Path(p)
            if path.exists() and path.is_dir():
                p, g = self._walk_path(path)
                executables += p
                dotdesktops += g

        return self._join_application_entries(executables, dotdesktops)


class DBExecutableFinder:
    def __init__(self, cfg: Configuration):
        pass

    def file_exists(self, filename) -> bool:
        return os.path.exists(filename)

    # TODO implement
    def create_app_from_db_instance(self, instance: db.Application) -> Application:
        try:
            if not self.file_exists(instance.path):
                return

            if ".desktop" not in instance.path:
                return PlainApplication()

            return XDGDesktopApplication()
        except Exception as e:
            logger.warning(e)
            raise e
    def walk(self) -> dict[str, Application]:
        db_apps: dict[str, Application] = {}

        app: db.Application
        for app in db.Application.select():
            db_apps[app.path] = self.create_app_from_db_instance(app)

        return db_apps

    def walk_by_frequency(self, count) -> list[str]:
        """Get paths of the most frequent N applications. """
        db_apps: list[str] = []

        app: db.Application
        for app in db.Application.select().order_by(db.Application.opened_count.desc()):
            if not self.file_exists(app.path):
                continue

            db_apps.append(app.path)

            if len(db_apps) == count:
                break

        return db_apps


class Engine:
    def __init__(self, cfg: Configuration):
        self.__executables: Optional[dict[str, Application]] = None

        self.__cfg = cfg
        self.__db_finder = DBExecutableFinder(self.__cfg)
        self.__fs_finder = FSExecutableFinder(self.__cfg)
        self.__executor = ThreadPoolExecutor(max_workers=1)
        self.__future = self.__executor.submit(self._init)

    @timeit
    def _init(self):
        fs_executables = self.__fs_finder.walk()
        db_executables = self.__db_finder.walk()
        self.__executables = fs_executables | db_executables

        # TODO implement the fuzzy search
        #  do approximate string matching based on bitap algorithm
        #  https://www.baeldung.com/cs/fuzzy-search-algorithm

    def get_executables(self):
        self.__future.result()
        return self.__executables

    # TODO implement
    def get_best_name_matches(self, partial_name, count) -> list[Application]:
        self.__future.result()
        pass

    # TODO implement 
    def get_best_path_matches(self, partial_path, count) -> list[Application]:
        self.__future.result()
        pass

    def get_most_recent_applications(self, count) -> list[Application]:
        self.__future.result()
        apps: list[Application] = []

        for app in self.__db_finder.walk_by_frequency(count):
            apps.append(self.__executables[app])

        return apps

    def reload(self):
        self.__future.result()

        self.__future = self.__executor.submit(self._init)
