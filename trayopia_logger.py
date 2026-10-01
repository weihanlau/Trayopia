import os
import builtins

log_path = os.getenv("TRAYOPIA_LOG_PATH")

_original_print = builtins.print


def print(*args, **kwargs):

    # Print normally to terminal
    _original_print(*args, **kwargs)

    # Also write to log
    if log_path:

        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")

        text = sep.join(str(arg) for arg in args) + end

        with open(log_path, "a", encoding="utf-8") as log:
            log.write(text)