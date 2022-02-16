from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import Callable, Optional, Union

from pls.args import args
from pls.data.getters import emoji_icons, nerd_icons
from pls.enums.icon_type import IconType
from pls.enums.node_type import NodeType, type_char_map, type_test_map
from pls.fs.git import formatted_status
from pls.fs.stats import (
    get_formatted_group,
    get_formatted_links,
    get_formatted_perms,
    get_formatted_size,
    get_formatted_time,
    get_formatted_user,
)
from pls.models.node_spec import NodeSpec
from pls.state import State


class Node:
    """
    A node is any file, folder or symlink on the file-system. This model stores
    attributes pertaining to a single FS node.

    Nodes are read from the file system directly using ``os.walk``.
    """

    def __init__(self, name: str, path: Path, state: Optional[State] = None):
        self.name = name
        self.path = path

        self.state = state  # keeping a copy to pass to dest_nodes

        # Git

        self.is_git_managed: bool = False
        self.path_wrt_git: Optional[Path] = None
        self.git_status: str = "  "
        if state is not None and state.is_git_managed:
            self.is_git_managed = True
            self.path_wrt_git = path.relative_to(state.git_root)
            self.git_status = state.git_status_map.get(self.path_wrt_git, "  ")

        # Stats

        self.stat: Optional[os.stat_result] = None
        try:
            self.stat = path.lstat()
            self.exists = True
        except FileNotFoundError:
            self.exists = False

        # Symlinks

        self.is_loop: bool = False  # only ``True`` for cyclic symlinks
        self.dest_node: Optional[Union[Node, str]] = None  # only populated for symlinks

        # Specs

        self.specs: list[NodeSpec] = []  # matched later (see ``map_specs``)

    def __eq__(self, other: object) -> bool:
        """
        Compare the object ``self`` to the other instance of ``Node``.

        :param other: the node to compare this node with for equality
        :return: ``True`` if the node instances are equal, ``False`` otherwise
        """

        if not isinstance(other, Node):
            return False
        return self.path.resolve() == other.path.resolve()

    def __repr__(self) -> str:
        """
        Get the string representation of the ``Node`` instance. This is also
        used by ``__str__`` automatically.

        :return: the string representation
        """

        return f"{self.name} @ {self.path}"

    @cached_property
    def node_type(self) -> NodeType:
        """whether the node is a file, folder, symlink, FIFO etc."""

        for node_type, node_type_test in type_test_map.items():
            if getattr(self.path, node_type_test)():
                # Symlinks need to set their destination node.
                if node_type == NodeType.SYMLINK and self.dest_node is None:
                    self.populate_dest()
                return node_type
        else:
            return NodeType.UNKNOWN

    @cached_property
    def pure_name(self) -> str:
        """the case-normalised name of the node with leading dots stripped"""

        return self.name.lstrip(".").lower()

    @cached_property
    def ext(self) -> str:
        """the extension of the node, i.e. the portion after the last dot"""

        return self.name.split(".")[-1] if "." in self.name else ""

    @cached_property
    def format_pair(self) -> tuple[str, str]:
        """the opening and closing tags of Rich console formatting markup"""

        format_rules = []

        # font color
        if not self.exists:
            format_rules.append("red")  # only happens for broken symlinks
        elif spec_color := self.spec_attr("color"):
            format_rules.append(str(spec_color))
        elif self.node_type == NodeType.DIR:
            format_rules.append("cyan")

        # font weight
        if spec_importance := self.spec_attr("importance"):
            if spec_importance == 2:
                format_rules.append("underline")
            elif spec_importance == 1:
                format_rules.append("bold")
            elif spec_importance == -1:
                format_rules.append("dim")
        elif self.is_git_managed:
            if self.git_status == "!!":  # Git-ignored file
                format_rules.append("dim")

        # italics
        if self.name == ".pls.yml":
            format_rules.append("italic")

        if format_rules:
            left = f"[{' '.join(format_rules)}]"
            right = "[/]"
        else:
            left = right = ""
        return left, right

    @cached_property
    def formatted_suffix(self) -> str:
        """the symbol after the filename representing its type"""

        if not self.exists:
            return "⚠"

        if self.node_type == NodeType.SYMLINK:
            assert self.dest_node is not None

            if self.is_loop:
                assert isinstance(self.dest_node, str)
                return f"[dim]@ ↺[/] [red]{self.dest_node}[/red]"

            assert isinstance(self.dest_node, Node)
            return f"[dim]@ →[/] {self.dest_node.formatted_name}"

        mapping = {
            NodeType.DIR: "/",
            NodeType.SOCKET: "=",
            NodeType.FIFO: "|",
        }
        suffix = mapping.get(self.node_type, "")
        if suffix:
            suffix = f"[dim]{suffix}[/]"
        return suffix

    @cached_property
    def formatted_name(self) -> str:
        """the name, formatted using Rich console formatting markup"""

        name = self.name
        if self.formatted_suffix:
            name = f"{name}{self.formatted_suffix}"

        if name.startswith(".") and not args.no_align:
            name = name.replace(".", "[dim].[/dim]", 1)

        # Apply format pair.
        left, right = self.format_pair
        return f"{left}{name}{right}"

    @cached_property
    def formatted_icon(self) -> str:
        """the emoji or Nerd Font icon to show beside the node"""

        if args.icon == IconType.NONE:
            return ""

        if args.icon == IconType.EMOJI:
            icon_index = emoji_icons
        else:  # args.icon == IconType.NERD
            icon_index = nerd_icons

        if spec_icon := self.spec_attr("icon"):
            icon = icon_index.get(str(spec_icon))
        elif self.node_type == NodeType.DIR:
            icon = icon_index.get("folder")
        else:
            icon = None

        if icon:
            # Apply format pair.
            left, right = self.format_pair
            icon = f"{left}{icon}{right}"
        else:
            icon = ""
        return icon

    @cached_property
    def formatted_git_status(self) -> str:
        """formatted two-letter Git status as returned by ``git-status``"""

        return formatted_status(self.git_status)

    @cached_property
    def is_visible(self) -> bool:
        """whether the node deserves to be rendered to the screen"""

        # If explicitly requested for all files, show all.
        if args.all:
            return True

        # Nodes without spec and with a leading dot are hidden.
        if not self.specs and self.name.startswith("."):
            return False

        # Nodes with importance -2 are hidden.
        if self.spec_attr("importance") == -2:
            return False

        return True

    @cached_property
    def type_char(self) -> str:
        """the single character representing the file type"""

        return type_char_map[self.node_type]

    @cached_property
    def table_row(self) -> Optional[dict[str, Optional[str]]]:
        """the mapping of column names and value when tabulating the node"""

        if not (self.exists and self.is_visible):
            return None
        assert self.stat is not None

        cells: dict[str, Optional[str]] = {}

        name = self.formatted_name
        if not self.name.startswith(".") and not args.no_align:
            # Left pad name with a space to account for leading dots.
            name = f" {name}"
        cells["name"] = name

        cells["icon"] = self.formatted_icon

        if not args.details:
            return cells  # return early as no more data needed

        cells["inode"] = str(self.stat.st_ino)
        cells["type"] = self.type_char
        column_function_map: dict[str, tuple[Callable, tuple]] = {
            "links": (get_formatted_links, ()),
            "perms": (get_formatted_perms, ()),
            "user": (get_formatted_user, ()),
            "group": (get_formatted_group, ()),
            "size": (get_formatted_size, ()),
            "ctime": (get_formatted_time, ("st_ctime",)),
            "mtime": (get_formatted_time, ("st_mtime",)),
            "atime": (get_formatted_time, ("st_atime",)),
        }
        for column, (function, func_args) in column_function_map.items():
            cells[column] = function(self.stat, *func_args)

        if self.is_git_managed:
            cells["git"] = self.formatted_git_status

        return cells

    def sort_key(self, field_name: str) -> Union[str, int, float]:
        """
        Get the value of the given field cleaned up in a way that enables it to
        be used for sorting the nodes.

        :param field_name: the name of the field by which to sort
        :return: the sort key formed by normalising the value of the field
        """

        field_value_map: dict[str, Union[str, int, float]] = {
            "name": self.pure_name,
            "ext": self.ext,
        }
        if self.stat is not None:
            field_value_map.update(
                {
                    "inode": self.stat.st_ino,
                    "links": self.stat.st_nlink,
                    "type": self.type_char,
                    "size": self.stat.st_size,
                    "ctime": self.stat.st_ctime,
                    "mtime": self.stat.st_mtime,
                    "atime": self.stat.st_atime,
                }
            )
        return field_value_map[field_name]

    def spec_attr(self, attr: str) -> Optional[Union[str, int]]:
        """
        Get the requested attribute from the first matching spec to provide it.

        :param attr: the requested attribute
        :return: the value of the attribute if found, ``None`` otherwise
        """

        for spec in self.specs:
            if attr_val := getattr(spec, attr, None):
                return attr_val
        return None

    def match(self, specs: list[NodeSpec]):
        """
        Find all spec matching this node from a list of all possible specs and
        store them in the ``specs`` attribute.

        :param specs: the list of all specs
        """

        self.specs = [spec for spec in specs if spec.match(self.name)]

    def populate_dest(self):
        """
        This sets the dest node for symlinks to a ``Node`` instance pointing to
        the next step in the link. This function ensures that the
        symlink is not unresolvable.
        """

        link_path = os.readlink(self.path)
        try:
            self.path.resolve()  # raises exception if cyclic

            # Use ``os.readlink`` instead of ``Path.resolve`` to step
            # through chained symlinks one-by-one.
            link = Path(link_path)
            if not link.is_absolute():
                link = self.path.parent.joinpath(link)

            self.dest_node = Node(name=link_path, path=link, state=self.state)
        except RuntimeError as exc:
            if "Symlink loop" in str(exc):
                self.is_loop = True
                self.dest_node = link_path