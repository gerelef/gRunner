import enum
import importlib.resources as ir


class XML(enum.StrEnum):
    ROOT = "root"
    TEMPLATE_MODAL = "template-modal"
    DIALOG_STACK = "dialog-stack"

    SETTINGS_BOX = "settings_box"
    APP_USAGE_BOX = "app_usage_box"
    ABOUT_BOX = "about_box"
    TEMPLATE_BOX = "gnome_template_box"
    GNOME_BTN = "gnome_template_btn"


def get_resource(resource: XML) -> str:
    return str(ir.files(__package__).joinpath(resource))
