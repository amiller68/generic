"""Widget operations.

Usage:
    from py_core import widget

    ctx = widget.process.Context(db=session, logger=logger)
    params = widget.process.Params(
        widget_id="...",
        on_started=my_on_started_callback,
        on_complete=my_on_complete_callback,
    )
    result = await widget.process.process_widget(params, ctx)
"""

from . import process

__all__ = ["process"]
