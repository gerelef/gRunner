import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Literal

from globals import autostr


@autostr
class Application(ABC):
    """Executable application."""

    def __init__(self, opened_count: int = 0, last_opened_utc: float = .0, first_opened_utc: float = .0):
        self.opened_count = opened_count
        self.last_opened_utc = last_opened_utc
        self.first_opened_utc = first_opened_utc

    def update_opened_count_meta(self, count: int):
        self.opened_count = count
        return self

    def update_last_opened_utc_meta(self, last_opened: float):
        self.last_opened_utc = last_opened
        return self

    def update_first_opened_utc_meta(self, first_opened: float):
        self.first_opened_utc = first_opened
        return self

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
# TODO implement activation from dbus
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
