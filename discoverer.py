import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import desktop_entry_lib as dtl
from loguru import logger

import db
from applications import PlainApplication, Application, XDGDesktopApplication
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


class Converter:

    @staticmethod
    def convert_executable_to_application(ap: ExecutableFile):
        return PlainApplication(str(ap.path))

    @staticmethod
    def convert_dotdesktop_to_application(dp: Path) -> Optional[Application]:
        df = dtl.DesktopEntry.from_file(dp)
        if df.Type == "Application" and df.should_show():
            return XDGDesktopApplication(dp, df.Name.get_translated_text(), df.Exec, df.Icon)
        return None


class Finder(ABC):

    @abstractmethod
    def walk(self):
        pass


@autostr
class FSExecutableFinder(Finder):
    # noinspection PyTypeChecker
    def __init__(self, cfg: Configuration):
        self.recursive: bool = cfg.get_recursive()
        self.paths: list[str] = cfg.get_paths()

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
                if app := Converter.convert_dotdesktop_to_application(dp):
                    dotdesktop_applications[str(dp)] = app

        self._filter_xdg_from_binary_entries(executables, dotdesktop_applications.values())

        for a in executables:
            if (dp := a.get_path()).exists():
                binary_applications[str(dp)] = Converter.convert_executable_to_application(a)

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


@autostr
class DBExecutableFinder(Finder):
    def __init__(self, cfg: Configuration):
        pass

    def _file_exists(self, filename) -> bool:
        return os.path.exists(filename)

    def _create_app_from_db_instance(self, instance: db.Application) -> Application:
        if not self._file_exists(instance.path):
            raise FileNotFoundError

        if ".desktop" not in instance.path:
            return PlainApplication(instance.path, instance.opened_count, instance.last_opened, instance.first_opened)

        return Converter.convert_dotdesktop_to_application(instance.path) \
            .update_opened_count_meta(instance.opened_count) \
            .update_last_opened_utc_meta(instance.last_opened) \
            .update_first_opened_utc_meta(instance.first_opened)

    def walk(self) -> dict[str, Application]:
        db_apps: dict[str, Application] = {}

        app: db.Application
        for app in db.Application.select():
            try:
                db_apps[app.path] = self._create_app_from_db_instance(app)
            except FileNotFoundError as e:
                logger.warning(e)
                continue

        return db_apps

    def walk_by_frequency(self, count) -> list[str]:
        """Get paths of the most frequent N applications. """
        db_apps: list[str] = []

        app: db.Application
        for app in db.Application.select().order_by(db.Application.opened_count.desc()):
            if not self._file_exists(app.path):
                logger.debug(f"file not found: {app.path}")
                continue

            db_apps.append(app.path)

            if len(db_apps) == count:
                break

        return db_apps
