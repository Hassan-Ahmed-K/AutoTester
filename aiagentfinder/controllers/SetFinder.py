import os
import time
import keyring
from dotenv import load_dotenv
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from aiagentfinder.utils.logger import Logger
from aiagentfinder.utils.workerThread import ThreadRunner
from PyQt5.QtCore import Qt

class SetFinderController:
    def __init__(self, ui):
        self.ui = ui
        self.runner = ThreadRunner()
        self.main_window = self.ui.parent()
        self.ui.htm_dir_btn.clicked.connect(self.browse_report_directory)
        self.ui.toggle_btn.stateChanged.connect(self.on_toggle_trade_filter)


    def browse_report_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self.ui,
            "Select htm Directory",
            os.getcwd()
        )

        if dir_path:
            # Check for at least one htm file in the selected directory
            report_files = [f for f in os.listdir(dir_path) if f.lower().endswith(".htm") ] #

            print(report_files)

            if len(report_files) > 0:
                self.ui.report_dir_input.setText(dir_path)
            else:
                QMessageBox.warning(
                    self.ui,
                    "No htm Files Found",
                    "The selected folder does not contain any HTML files.\n"
                    "Please select a valid folder containing HTML files."
                )


    def on_toggle_trade_filter(self, state):
        """Show/hide inputs based on toggle state."""
        # return
        if state == Qt.Checked:
            self.ui.target_dd_widget.hide()
            self.ui.risk_trade_widget.show()
            self.ui.max_consec_loss_widget.show()
            self.ui.filter_row.setStretch(
            self.ui.filter_row.indexOf(self.ui.dynamic_container), 2
        )
        else:
            self.ui.target_dd_widget.show()
            self.ui.risk_trade_widget.hide()
            self.ui.max_consec_loss_widget.hide()
            self.ui.filter_row.setStretch(
            self.ui.filter_row.indexOf(self.ui.dynamic_container), 1
        )