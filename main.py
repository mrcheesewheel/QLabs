

import controller
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
controller = controller.MainController()
controller.run()
app.exec()








