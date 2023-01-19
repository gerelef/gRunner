import enum
import importlib.resources as ir


class XML(enum.StrEnum):
    ROOT = "root"
    MODAL = "modal"
    SETTINGS_BOX = "settings_box"
    APP_USAGE_BOX = "app_usage_box"
    ABOUT_BOX = "about_box"


def get_resource(resource: XML) -> str:
    return str(ir.files(__package__).joinpath(resource))
