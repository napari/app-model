from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Tuple, Type, Union, cast

from qtpy.QtWidgets import QAction

from app_model import Application

from ._qkeymap import QKeyBindingSequence
from ._util import to_qicon

if TYPE_CHECKING:
    from qtpy.QtCore import QObject

    from app_model.types import CommandRule, MenuItem


class QCommandAction(QAction):
    """Base QAction for a command id. Can execute the command.

    Parameters
    ----------
    command_id : str
        Command ID.
    app : Union[str, Application]
        Application instance or name of application instance.
    parent : Optional[QWidget]
        Optional parent widget, by default None
    """

    def __init__(
        self,
        command_id: str,
        app: Union[str, Application],
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._app = Application.get_or_create(app) if isinstance(app, str) else app
        self._command_id = command_id
        self.setObjectName(command_id)
        if kb := self._app.keybindings.get_keybinding(command_id):
            self.setShortcut(QKeyBindingSequence(kb.keybinding))
        self.triggered.connect(self._on_triggered)

    def _on_triggered(self, checked: bool) -> None:
        self._app.commands.execute_command(self._command_id)


class QCommandRuleAction(QCommandAction):
    """QAction for a CommandRule.

    Parameters
    ----------
    command_id : str
        Command ID.
    app : Union[str, Application]
        Application instance or name of application instance.
    parent : Optional[QWidget]
        Optional parent widget, by default None
    """

    def __init__(
        self,
        command_rule: CommandRule,
        app: Union[str, Application],
        parent: Optional[QObject] = None,
        *,
        use_short_title: bool = False,
    ):
        super().__init__(command_rule.id, app, parent)
        self._cmd_rule = command_rule
        if use_short_title and command_rule.short_title:
            self.setText(command_rule.short_title)  # pragma: no cover
        else:
            self.setText(command_rule.title)
        if command_rule.icon:
            self.setIcon(to_qicon(command_rule.icon))
        if command_rule.tooltip:
            self.setToolTip(command_rule.tooltip)
        if command_rule.status_tip:
            self.setStatusTip(command_rule.status_tip)

    def update_from_context(self, ctx: Mapping[str, object]) -> None:
        """Update the enabled state of this menu item from `ctx`."""
        self.setEnabled(expr.eval(ctx) if (expr := self._cmd_rule.enablement) else True)


class QMenuItemAction(QCommandRuleAction):
    """QAction for a MenuItem.

    Mostly the same as a CommandRuleAction, but aware of the `menu_item.when` clause
    to toggle visibility.
    """

    _cache: Dict[Tuple[int, int], QMenuItemAction] = {}

    def __new__(
        cls: Type[QMenuItemAction],
        menu_item: MenuItem,
        app: Union[str, Application],
        **kwargs: Any,
    ) -> QMenuItemAction:
        """Create and cache a QMenuItemAction for the given menu item."""
        cache = kwargs.pop("cache", True)
        app = Application.get_or_create(app) if isinstance(app, str) else app
        key = (id(app), hash(menu_item))
        if cache and key in cls._cache:
            return cls._cache[key]

        self = cast(QMenuItemAction, super().__new__(cls))
        if cache:
            cls._cache[key] = self
        return self

    def __init__(
        self,
        menu_item: MenuItem,
        app: Union[str, Application],
        parent: Optional[QObject] = None,
        *,
        cache: bool = True,
    ):
        initialized = False
        with contextlib.suppress(RuntimeError):
            initialized = getattr(self, "_initialized", False)

        if not initialized:
            super().__init__(menu_item.command, app, parent)
            self._menu_item = menu_item
            key = (id(self._app), hash(menu_item))
            self.destroyed.connect(lambda: QMenuItemAction._cache.pop(key, None))
            self._app.destroyed.connect(lambda: QMenuItemAction._cache.pop(key, None))
            self._initialized = True

    def update_from_context(self, ctx: Mapping[str, object]) -> None:
        """Update the enabled/visible state of this menu item from `ctx`."""
        super().update_from_context(ctx)
        self.setVisible(expr.eval(ctx) if (expr := self._menu_item.when) else True)

    def __repr__(self) -> str:
        name = self.__class__.__name__
        return f"{name}({self._menu_item!r}, app={self._app.name!r})"
