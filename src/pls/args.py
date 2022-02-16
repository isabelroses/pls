import argparse
import os
from pathlib import Path
from typing import Optional

from pls import __version__
from pls.enums.icon_type import IconType
from pls.enums.unit_system import UnitSystem
from pls.exceptions import ExecException
from pls.table.detail_columns import detail_columns


detail_column_keys = detail_columns.keys()

##########
# Parser #
##########

parser = argparse.ArgumentParser(
    prog="pls",
    description=(
        """
        `pls` is a prettier `ls` for the pros.
        You can read the docs at https://dhruvkb.github.io/pls and
        obtain the source code at https://github.com/dhruvkb/pls.
        """
    ),
    add_help=False,  # added via the 'meta' group later
)

########################
# Positional arguments #
########################


def directory(path_str: str) -> Path:
    """
    Parse the given path into a ``Path`` instance. The path is considered valid
    if it points to an existing directory.

    :param path_str: the path supplied as a CLI argument
    :return: the ``Path`` instance wrapping the supplied path
    :raise: ``ExecException``, if the path is invalid
    """

    path = Path(path_str).resolve()
    if not os.path.isdir(path):
        raise ExecException("`directory` must be a path to a directory")
    return path


parser.add_argument(
    "directory",
    type=directory,
    nargs="?",  # makes the `directory` arg optional
    default=os.getcwd(),
    help="the directory whose contents are to be listed",
)

########
# Meta #
########

meta = parser.add_argument_group(
    title="meta",
    description="meta-arguments for `pls` itself",
)
meta.add_argument(
    *["-h", "--help"],
    action="help",
    help="show this help message and exit",
)
meta.add_argument(
    *["-v", "--version"],
    action="version",
    version=f"%(prog)s {__version__}",
    help="show the version of the codebase",
)

################
# Presentation #
################

presentation = parser.add_argument_group(
    title="presentation",
    description="arguments for controlling the presentation of nodes",
)
presentation.add_argument(
    *["-i", "--icon"],
    type=IconType,
    choices=list(IconType),
    default=IconType.NERD,
    help="the type of icons to show with the files",
)
presentation.add_argument(
    "--no-align",
    action="store_true",
    help="turn off character alignment for leading dots",
)

########
# Info #
########


class DetailsAction(argparse.Action):
    """
    Slightly modified ``_AppendAction`` to deal with sets. This allows ``const``
    to be a set that is merged with the ``dest`` set instead of nested in it.
    """

    def __call__(self, parser, namespace, value, option_string=None):
        items = getattr(namespace, self.dest, None)

        if items is None:
            items = set()
        elif isinstance(items, set):
            items = set(items)

        if isinstance(value, set):
            # ``--details`` flag without values means ``value`` = ``const``
            items.update(value)
        else:
            # add each ``value`` to ``items``
            items.add(value)

        setattr(namespace, self.dest, items)


info = parser.add_argument_group(
    title="info",
    description="arguments for controlling the amount of info for nodes",
)
info.add_argument(
    *["-d", "--details"],
    action=DetailsAction,
    nargs="?",
    dest="details",
    help="the data points to show for each node in the output",
    default=None,  # when there is no --details flag
    const={"type", "perms"},  # when there is a --details flag without value
    choices={"+"}.union(detail_columns.keys()),  # + means all
)

#####################
# Info modification #
#####################

info_mod = parser.add_argument_group(
    title="info modification",
    description="arguments for modifying the presentation of information",
)
info_mod.add_argument(
    *["-u", "--units"],
    type=UnitSystem,
    choices=list(UnitSystem),
    default=UnitSystem.BINARY,
    help="the units to use when listing the size of files",
)
info_mod.add_argument(
    *["-t", "--time_fmt"],
    type=str,
    default="[dim]%Y-[/]%m-%d %H:%M[dim]:%S ",
    help="the template for formatting the timestamps on the file",
)

###########
# Sorting #
###########

invalid_keys = {"perms", "user", "group", "git"}
sort_choices = ["name", "ext"]
sort_choices += [item for item in detail_column_keys if item not in invalid_keys]
sort_choices += [f"{key}-" for key in sort_choices]

sorting = parser.add_argument_group(
    title="sorting",
    description="arguments used for sorting nodes in the output",
)
sorting.add_argument(
    *["-s", "--sort"],
    help="the field based on which to sort the files and directories",
    default="name",
    choices=sort_choices,
)
sorting.add_argument(
    "--no-dirs-first",
    action="store_true",
    help="mix directories and files, sorting them together",
)

#############
# Filtering #
#############

filtering = parser.add_argument_group(
    title="filtering",
    description="arguments used for filtering nodes in the output",
)
filtering.add_argument(
    "--all",
    action="store_true",
    help="show all files, including those that would otherwise be hidden",
)
filtering.add_argument(
    "--no-dirs",
    action="store_true",
    help="hide directories in the output",
)
filtering.add_argument(
    "--no-files",
    action="store_true",
    help="hide files in the output",
)

#################
# Configuration #
#################

configuration = parser.add_argument_group(
    title="configuration",
    description="arguments for controlling `pls` using config files",
)
configuration.add_argument(
    *["--depth"],
    type=int,
    default=4,
    help="the max depth upto which to look for a `.pls.yml` file",
)

#############
# Exporting #
#############


def file(path_str: str) -> Optional[Path]:
    """
    Parse the given path into a ``Path`` instance. The path is considered valid
    if nothing exists there or if it points to a file.

    :param path_str: the path supplied as a CLI argument
    :return: the ``Path`` instance wrapping the supplied path if it is valid,
        ``None`` otherwise
    """

    path = Path(path_str).resolve()
    if not path.exists() or (path.exists() and path.is_file()):
        return path
    else:
        return None


exporting = parser.add_argument_group(
    title="exporting",
    description="arguments for exporting the output to a file",
)
exporting.add_argument(
    *["-e", "--export"],
    type=file,
    default=None,
    help="the path to the file where to write the exported HTML",
)


args = parser.parse_args()
"""the CLI arguments parsed by ``argparse``"""

__all__ = ["args"]