import sys
import os
import multiprocessing
import runpy
import warnings
import traceback

# 1. SILENCE WARNINGS
warnings.filterwarnings("ignore")

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QCoreApplication

from src.devicemanagement.device_manager import DeviceManager
from src.tweaks.tweak_loader import load_daemons

if __name__ == "__main__":
    multiprocessing.freeze_support()

    # 2. CLI DISPATCHER
    # The frozen app re-invokes itself as a Python interpreter for some
    # pymobiledevice3 background processes. This keeps that behavior.
    if len(sys.argv) > 1:
        if '-m' in sys.argv:
            try:
                m_index = sys.argv.index('-m')
                sys.argv = sys.argv[m_index + 1:]
                module_name = sys.argv[0]
                try:
                    runpy.run_module(module_name, run_name="__main__", alter_sys=True)
                except ImportError as e:
                    if "cannot be directly executed" in str(e) or "No module named" in str(e):
                        runpy.run_module(f"{module_name}.__main__", run_name="__main__", alter_sys=True)
                    else:
                        raise
            except Exception as e:
                sys.stderr.write(f"Background Process Crash: {e}\n")
                traceback.print_exc()
            sys.exit()

        first_arg = sys.argv[1]
        if first_arg.endswith('.py'):
            sys.argv = sys.argv[1:]
            try:
                runpy.run_path(sys.argv[0], run_name="__main__")
            except Exception as e:
                sys.stderr.write(f"Script Crash: {e}\n")
                traceback.print_exc()
            sys.exit()

    # 3. GUI STARTUP
    print("Starting UnRestrict...")

    # route print() / library logging into the live log box
    from src.gui.log_bus import install_capture
    install_capture()

    app = QtWidgets.QApplication([])

    QCoreApplication.setOrganizationDomain("com.unrestrict")
    QCoreApplication.setApplicationName("UnRestrict")

    # register the daemon tweaks used by the whole app
    load_daemons()

    dm = DeviceManager()

    icon_path = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(__file__)),
                             "files", "unrestrict.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QtGui.QIcon(icon_path))

    from src.gui.main_window import MainWindow
    widget = MainWindow(device_manager=dm)
    widget.show()

    print("UnRestrict launched.")
    sys.exit(app.exec())
