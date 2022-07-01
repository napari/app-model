from __future__ import annotations

from typing import TYPE_CHECKING, Mapping, Optional, Union

from qtpy.QtWidgets import QAction

from app_model import Application

if TYPE_CHECKING:
    from qtpy.QtCore import QObject
    from qtpy.QtGui import QIcon

    from app_model.types import CommandIdStr, CommandRule, Icon, MenuItem


def to_qicon(icon: Icon) -> QIcon:
    """Create QIcon from Icon."""
    from superqt import fonticon

    assert icon.dark
    return fonticon.icon(icon.dark)


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
        command_id: CommandIdStr,
        app: Union[str, Application],
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self._app = Application.get_or_create(app) if isinstance(app, str) else app
        self._command_id = command_id
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
        self.setObjectName(command_rule.id)
        if use_short_title:
            self.setText(command_rule.short_title)
        else:
            self.setText(command_rule.title)
        if command_rule.icon:
            self.setIcon(to_qicon(command_rule.icon))
        if command_rule.tooltip:
            self.setToolTip(command_rule.tooltip)

    def update_from_context(self, ctx: Mapping[str, object]) -> None:
        """Update the enabled state of this menu item from `ctx`."""
        self.setEnabled(expr.eval(ctx) if (expr := self._cmd_rule.enablement) else True)


class QMenuItemAction(QCommandRuleAction):
    """QAction for a MenuItem."""

    def __init__(
        self,
        menu_item: MenuItem,
        app: Union[str, Application],
        parent: Optional[QObject] = None,
    ):
        super().__init__(menu_item.command, app, parent)
        self._item = menu_item

    def update_from_context(self, ctx: Mapping[str, object]) -> None:
        """Update the enabled/visible state of this menu item from `ctx`."""
        super().update_from_context(ctx)
        self.setVisible(expr.eval(ctx) if (expr := self._item.when) else True)
