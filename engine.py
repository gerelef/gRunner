from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from applications import Application
from discoverer import DBExecutableFinder, FSExecutableFinder
from globals import timeit, Configuration


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
