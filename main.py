import sys
import tempfile
import subprocess
import os

try:
    from PyQt5.QtCore import Qt, QT_VERSION_STR, QDateTime, QCoreApplication, QRect, QThread, pyqtSignal, QProcess
    from PyQt5.QtGui import QImage, QIntValidator, QValidator
    from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QDialog, QVBoxLayout, QDialogButtonBox, \
        QDateTimeEdit, QTextEdit, QPlainTextEdit, QLineEdit, QLabel, QStyle, QCheckBox, QHBoxLayout, QGridLayout, \
        QMessageBox, QAbstractButton, QWizard, QWizardPage, QComboBox
except ImportError:
    raise ImportError("Requires PyQt5.")
from QtImagePartSelector import QtImagePartSelector

WKHTMLTOIMAGE = "wkhtmltoimage"
XVFB = "xvfb-run"
XVFB_BASE_PARAMETERS = ["-a", "-s", "-screen 0 640x480x16", WKHTMLTOIMAGE]

try:
    subprocess.run(WKHTMLTOIMAGE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    raise FileNotFoundError("wkhtmltopdf must be installed on system")

try:
    subprocess.run(XVFB, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    raise FileNotFoundError("xvfb must be installed on system")

PATH_MD5_SCRIPT = "pyvisualcompare-md5.sh"


class NotEmptyValidator(QValidator):
    def validate(self, text: str, pos):
        if bool(text.strip()):
            state = QValidator.Acceptable
        else:
            state = QValidator.Intermediate  # so that field can be made empty temporarily
        return state, text, pos


class UrlDialog(QDialog):
    def __init__(self, parent=None):
        super(UrlDialog, self).__init__(parent)
        self.setWindowTitle("Enter URL")

        vbox = QVBoxLayout(self)

        grid = QGridLayout()
        vbox.addLayout(grid)

        grid.addWidget(QLabel("URL of web page"), 0, 0)

        self.url_edit = QLineEdit(self)
        self.url_edit.setPlaceholderText("https://duckduckgo.com")
        self.url_edit.textChanged.connect(self.lineEditTextChanged)
        self.url_edit.setValidator(NotEmptyValidator())
        self.url_edit.setToolTip("Must not be empty")
        grid.addWidget(self.url_edit, 0, 1)

        grid.addWidget(QLabel("Static size"), 1, 0)
        self.static_size_edit = QCheckBox()
        self.static_size_edit.stateChanged.connect(self.staticSizeChanged)
        grid.addWidget(self.static_size_edit, 1, 1)

        grid.addWidget(QLabel("Width of page"), 2, 0)
        self.width_edit = QLineEdit()
        self.width_edit.setText("1280")
        self.width_edit.setValidator(QIntValidator(640, 20000))
        self.width_edit.setToolTip("Must be between 640 and 20000")
        self.width_edit.textChanged.connect(self.lineEditTextChanged)
        self.width_edit.setDisabled(True)
        grid.addWidget(self.width_edit, 2, 1)

        grid.addWidget(QLabel("Height of page"), 3, 0)
        self.height_edit = QLineEdit()
        self.height_edit.setText("1024")
        self.height_edit.setValidator(QIntValidator(480, 20000))
        self.height_edit.setToolTip("Must be between 480 and 20000")
        self.height_edit.textChanged.connect(self.lineEditTextChanged)
        self.height_edit.setDisabled(True)
        grid.addWidget(self.height_edit, 3, 1)

        grid.addWidget(QLabel("Delay before screenshot [ms]"), 4, 0)
        self.delay_edit = QLineEdit()
        self.delay_edit.setText("350")
        self.delay_edit.setValidator(QIntValidator(200, 20000))
        self.delay_edit.setToolTip("Must be between 200 and 20000")
        self.delay_edit.textChanged.connect(self.lineEditTextChanged)
        grid.addWidget(self.delay_edit, 4, 1)

        # OK and Cancel buttons
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        vbox.addWidget(self.buttons)

        # initially disable OK button b/c no URL has been entered yet
        self.buttons.buttons()[0].setDisabled(True)

    def staticSizeChanged(self, enable):
        self.width_edit.setDisabled(not enable)
        self.height_edit.setDisabled(not enable)

        if not enable:
            # reset default values of fields below so that invalid values do not keep the user from proceeding
            self.width_edit.setText("1280")
            self.height_edit.setText("1024")

    def lineEditTextChanged(self, *args, **kwargs):
        """ After user edits a QLineEdit, set a color according to the field's current validity """
        sender = self.sender()
        state = self.getLineEditValidity(sender)
        if state == QValidator.Acceptable:
            sender.setStyleSheet("")  # reset background to default
        else:
            color = '#f6989d'  # red
            sender.setStyleSheet("QLineEdit {{ background-color: {} }}".format(color))

        # check whether all fields are acceptable
        all_fields_valid = True
        for line_edit in [self.url_edit, self.width_edit, self.height_edit, self.delay_edit]:
            if not self.getLineEditValidity(line_edit) == QValidator.Acceptable:
                all_fields_valid = False
                break

        # disable OK button if not all fields are valid
        self.buttons.buttons()[0].setDisabled(not all_fields_valid)

    @staticmethod
    def getLineEditValidity(line_edit: QLineEdit) -> QValidator.State:
        validator = line_edit.validator()
        state = validator.validate(line_edit.text(), 0)[0]
        return state

    @staticmethod
    def getUrl(parent=None):
        dialog = UrlDialog(parent)
        result = dialog.exec_()

        resultdict = {
            "ok": result == QDialog.Accepted,
            "url": dialog.url_edit.text(),
            "static_size": dialog.static_size_edit.isChecked(),
            "height": dialog.height_edit.text(),
            "width": dialog.width_edit.text(),
            "delay": dialog.delay_edit.text()
        }

        return resultdict

class LabelAndTextfieldPage(QWizardPage):
    def __init__(self, parent, labelstr, textfieldstr):
        super(LabelAndTextfieldPage, self).__init__(parent)

        layout = QVBoxLayout()
        label = QLabel(
            labelstr
        )

        label.setWordWrap(True)
        layout.addWidget(label)

        textfield = QTextEdit()
        textfield.setReadOnly(True)
        textfield.setText(textfieldstr)
        layout.addWidget(textfield)

        self.setLayout(layout)


class MagicWizard(QWizard):
    def __init__(self, parent, urlwatch_config):
        super(MagicWizard, self).__init__(parent)

        self.addPage(LabelAndTextfieldPage(self,
                                           "An area of interest was successfully selected. To automatically watch that "
                                           "area for changes, "
                                           "some further actions are necessary.\n"
                                           "\n"
                                           "It is recommended to run everything on a dedicated Linux server. "
                                           "This wizard will guide you through the setup process. If you are only "
                                           "interested in the urlwatch config, you can find that below.",
                                           urlwatch_config
                                           ))

        self.addPage(LabelAndTextfieldPage(self,
                                           "urlwatch, wkhtmltopdf and xvfb need to be installed on the server.\n"
                                           "urlwatch is necessary to watch out for changes and send notifications.\n"
                                           "wkhtmltopdf is a tool to render a web page into PDF or image files "
                                           "(similar to a browser).\n"
                                           "Lastly, xvfb is needed so that no complete X11 display server needs to "
                                           "be installed. \n\n"
                                           "On Ubuntu or Debian systems, these "
                                           "applications can be installed with the following command:",

                                           "$ sudo apt install urlwatch wkhtmltopdf xvfb"
                                           ))
        self.addPage(LabelAndTextfieldPage(self,
                                           "Login on your server as the user that is supposed to run urlwatch and "
                                           "send notifications.",

                                           "$ su urlwatcher"))

        self.addPage(LabelAndTextfieldPage(self, "Open the urlwatch config in your text editor, clear the "
                                                 "example configuration if there is any and paste the "
                                                 "configuration below.",

                                           "$ urlwatch - -edit\n\n"
                                           ""
                                           "{}".format(urlwatch_config)))

        self.addPage(LabelAndTextfieldPage(self,
                                           "Save the urlwatch config and set the correct "
                                           "file permissions for urlwatch:",

                                           "$ chmod 700 -R ~/.config/urlwatch/"))
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), PATH_MD5_SCRIPT), "r") as f:
            script_content = f.read()

        self.addPage(LabelAndTextfieldPage(self,
                                           "To simplify quite a lot of things, a simple script must be installed on "
                                           "the server. You should put it into the file "
                                           "/usr/local/bin/pyvisualcompare-md5.sh. Make sure to mark it as "
                                           "executable.",

                                           script_content))

        self.addPage(LabelAndTextfieldPage(self,
                                           "Configure urlwatch to your liking, e.g. to send mail notifications. "
                                           "Details can be found in the urlwatch docs.",

                                           "https://github.com/thp/urlwatch"
                                           ))

        self.addPage(LabelAndTextfieldPage(self,
                                           "Nearly finished! You should probably add a cronjob to regularly call "
                                           "urlwatch. Note that a cronjob usually runs in a very restricted "
                                           "environment, so you should probably also add /usr/local/bin to your PATH "
                                           "variable and set your default shell to bash. "
                                           "An example for calling urlwatch every 10 minutes would be as follows:",

                                           "$ crontab -e\n\n"
                                           ""
                                           "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games\n"
                                           "SHELL=/bin/bash\n"
                                           "# m h  dom mon dow   command\n"
                                           "*/10 * * * * urlwatch"))

        self.addPage(LabelAndTextfieldPage(self,
                                           "Now we are done! On newer version of urlwatch (>= 2.13) you can test "
                                           "your urlwatch filter manually. It should always return the same "
                                           "MD5 hash - except when a change was made in the area of interest.\n\n"
                                           "If the area of interest gets moved because new content is added above, "
                                           "your filter will still notice a change. If that is not the desired "
                                           "behavior, you can have a look at the other urlwatch filters available.",

                                           "$ urlwatch --test-filter 1"
                                           ))

        self.setWindowTitle("Server setup wizard")
        self.resize(640, 480)


class MyMainWindow(QMainWindow):

    def __init__(self):
        super(MyMainWindow, self).__init__()

        self.graphicsView = QtImagePartSelector()
        self.setCentralWidget(self.graphicsView)

        self.graphicsView.rectSet.connect(self.onRectSet)

        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        load_url_action = file_menu.addAction("Load from URL")
        load_url_action.triggered.connect(self.getImage)

        close_action = file_menu.addAction("Quit")
        close_action.triggered.connect(self.close)

        self.confirm_area_action = menubar.addAction('Confirm area')
        self.confirm_area_action.setDisabled(True)
        self.confirm_area_action.triggered.connect(self.onConfirm)
        # self.confirm_area_action.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogApplyButton))

        self.statusBarWidget = QLabel()
        self.statusBar().addWidget(self.statusBarWidget)
        self.statusBarWidget.setText("Ready to load URL")

        self.tempdir = tempfile.mkdtemp()
        self.tempfilename = os.path.join(self.tempdir, "pyvisualcompare.png")

        self.selected_rectangle = None

        self.url_dict = None

        self.resize(500, 300)

        self.setWindowTitle('pyvisualcompare')

    def getUrlwatchConfig(self):
        s = "name: ExampleName\n" \
            "kind: shell\n" \
            "command: pyvisualcompare-md5.sh"

        s += " --crop-x {} --crop-y {} --crop-w {} --crop-h {} ".format(
            self.selected_rectangle.topLeft().x(),
            self.selected_rectangle.topLeft().y(),
            self.selected_rectangle.width(),
            self.selected_rectangle.height()
        )

        s += " ".join(self.getWkhtmlParameters())
        s += "\n---"

        return s

    def getWkhtmlParameters(self):
        # generate only parameters passed to wkhtmltoimage (except destination filename) to get full screenshot
        parameters = []

        if self.url_dict["static_size"]:
            parameters.append("--height")
            parameters.append(self.url_dict["height"])
            parameters.append("--width")
            parameters.append(self.url_dict["width"])

        # add delay
        parameters.append("--javascript-delay")
        parameters.append(self.url_dict["delay"])

        parameters.append(self.url_dict["url"])

        return parameters

    def getXvfbParameters(self):
        # generate complete parameter set for xvfb call

        parameters = XVFB_BASE_PARAMETERS.copy()
        # append wkhtmltoimage parameters
        parameters += self.getWkhtmlParameters()
        parameters.append(self.tempfilename)

        return parameters

    def getImage(self):
        self.url_dict = UrlDialog.getUrl(self)

        if self.url_dict["ok"]:
            self.statusBarWidget.setText("Loading page...")
            self.graphicsView.clearImage()
            self.confirm_area_action.setDisabled(True)
            self.selected_rectangle = None

            self.process = QProcess()
            self.process.finished.connect(self.getImageCallback)

            self.process.start(XVFB, self.getXvfbParameters())

    def getImageCallback(self, returncode):
        msg = QMessageBox(self)

        if returncode == 0:
            image = QImage(self.tempfilename)
            self.graphicsView.setImage(image)
            self.resize(min(image.width() + 64, 1400), min(image.height() + 64, 800))
            self.statusBarWidget.setText("Drag or zoom with middle button and select area of interest. "
                                         "Afterwards confirm area in menu.")

            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Screenshot loaded")
            msg.setText("A screenshot was successfully loaded.")
            msg.setInformativeText("1. Drag or zoom the image with the middle button and mousewheel. \n"
                                   "2. Select area of interest by left-clicking and dragging. \n"
                                   "3. Finally, confirm the area.")

        else:
            self.statusBarWidget.setText("Error while loading page")

            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Error while loading page")
            msg.setText("There was an error while loading the page.")
            msg.setInformativeText("The URL was possibly incorrect. "
                                   "Also, some pages cannot be loaded without specifying a static size - "
                                   "so you might want to try that.")
            msg.setDetailedText(
                "Standard output:\n\n{}\n\n--\nError output:\n\n{}".format(
                    bytes(self.process.readAllStandardOutput()).decode(),
                    bytes(self.process.readAllStandardError()).decode()
                ))

        msg.exec_()

    def onConfirm(self, event):
        wizard = MagicWizard(self, self.getUrlwatchConfig())
        wizard.exec_()

    def onRectSet(self, r: QRect):
        """Rectangle has been selected"""
        self.selected_rectangle = r
        if self.graphicsView.hasImage() and r.width() > 1 and r.height() > 1:
            self.confirm_area_action.setDisabled(False)
        else:
            self.confirm_area_action.setDisabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    window = MyMainWindow()
    window.show()
    # open URL dialog at start
    window.getImage()

    sys.exit(app.exec_())
