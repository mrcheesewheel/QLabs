
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QTextCursor,QFont,QFontDatabase, QColor,QIcon
from PyQt5 import QtCore
from gate import *

class MainWindow(QWidget):
    """Main window of the program, it handles the subviews and is informed by the controller"""

    def __init__(self):
        """initialises the view components of the main window in the program"""
        super().__init__()

        self.vboxRoot = QVBoxLayout()

        self.setWindowTitle("QLab")

        self.toolbar = QToolBar()
        
        newtb = QAction("Reset",self)
        savetb = QAction("Save",self)
        opentb = QAction("Load",self)
        newgatetb = QAction("New_gate",self)
        removeregtb = QAction("Remove_qubit",self)
        addregtb = QAction("Add_qubit",self)
        optionstb = QAction("View_options",self)

        self.toolbar.addAction(newtb)
        self.toolbar.addAction(savetb)
        self.toolbar.addAction(opentb)
        self.toolbar.addAction(newgatetb)
        self.toolbar.addAction(removeregtb)
        self.toolbar.addAction(addregtb)
        self.toolbar.addAction(optionstb)

        self.vboxRoot.addWidget(self.toolbar)

        self.hboxMainViews = QHBoxLayout()        
        self.vboxRoot.addLayout(self.hboxMainViews)
        self.dv = DiagramView()
        self.cv = CodeView()
        self.vboxRoot.addWidget(self.dv.registers)
        self.hboxMainViews.addWidget(self.dv.qgate_list_widget)
        self.hboxMainViews.addWidget(self.dv.matrix_preview)
        self.hboxMainViews.addWidget(self.cv)

        self.setLayout(self.vboxRoot)

    def on_click_newGate(self):
        """creates a new instance of the new gate popup and shows it"""
        self.window = NewGatePopup()
        self.window.show()

    def on_click_editGate(self,gate):
        """creates a new instance of the edit gate pop up and shows it
        parameters:
            gate (Gate): reference to the specified Gate object"""
        self.window = GateInfoPopup(gate)
        self.window.show()

    def on_click_options(self,f,col):
        """creates a new instance of the accessibility options and shows it
        parameters:
            f (String): name of the current font family 
            col (String): name of the current highlight colour"""
        self.window = OptionsPopup(f,col)
        self.window.show()

    def save_file(self):
        """Allows the user to save a file containing the current entry in the code box"""
        name = QFileDialog.getSaveFileName(self, 'Save File')
        file = open(name[0],'w')
        text = self.cv.code_box.toPlainText()
        file.write(text)
        file.close()

    def load_file(self):
        """Allows the user to load a file of text into the code box"""
        name = QFileDialog.getOpenFileName(self, 'Load File')
        
        file = open(name[0],'r')
        code = file.read()
        self.cv.code_box.clear()
        self.cv.code_box.appendPlainText(code)
        file.close()

    def error_popup(self,text):
        """Creates a generic error and enters the text parameter in as the message
        parameters:
            text (String): the error message to come up"""
        self.errorer = QMessageBox()
        self.errorer.setIcon(QMessageBox.Critical)
        self.errorer.setText(text)
        self.errorer.setWindowTitle("Error")
        self.errorer.setStandardButtons(QMessageBox.Ok)
        self.errorer.show()

class DiagramView(QWidget):
    """a subview of the view classes, it is responsible for the quantum circuit table and the list of operations"""

    def __init__(self):
        """Initialises the gate list and table to their default values"""
        super().__init__()        

        self.vboxR = QVBoxLayout()
        self.hboxT = QHBoxLayout()
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout()
        self.vboxR.addLayout(self.hboxT)
        self.vboxR.addLayout(self.hbox)       
        
        self.qgate_list_widget = QListWidget()
        self.hbox.addWidget(self.qgate_list_widget)  
        self.qgate_list_widget.setAcceptDrops(True)
        self.qgate_list_widget.setDragEnabled(True)   

        self.matrix_preview = QTableWidget()
        self.matrix_preview.setEditTriggers(QTableWidget.NoEditTriggers)
        
        
        self.registers = QTableWidget()
        self.registers.setSelectionMode(QAbstractItemView.SingleSelection)
        self.registers.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.registers.setAcceptDrops(True)
        self.registers.setDragEnabled(True)
        self.registers.setEditTriggers(QTableWidget.NoEditTriggers)
        
        
        self.vbox.addWidget(self.registers)
        
        #self.registers.setShowGrid(False)

        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.setLayout(self.vboxR)

    def reset_column_sizes(self,m):
        """Resets the column size to the size of the biggest entry """
        temp = []
        for i in range(self.registers.columnCount()):
            temp.append(self.registers.sizeHintForColumn(i))

        #max_width = max(temp)
        temp.append(15*m)
        max_width = max(temp)
        for i in range(self.registers.columnCount()):
            self.registers.setColumnWidth(i,max_width)

        

class NewGatePopup(QWidget):
    """Responsible for presenting the options for creating a new gate"""

    def __init__(self):
        """Declares the fields necessary for the creation of a new gate"""
        
        super().__init__()
        layout = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()
        self.setWindowTitle("Gate editor")
        self.name = QLineEdit()
        self.multiplier = QLineEdit()
        self.multiplier.setText("1")
        self.qubitscount = QSpinBox()
        self.qubitscount.setMinimum(1)
        self.img_chooser = QPushButton("Choose image")
        self.assocs = QTableWidget()
        self.assocs.setRowCount(0)
        self.assocs.setColumnCount(1)
        self.assocs.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.saveG = QPushButton("Save Gate")

        self.matr = QTableWidget()
        self.matr.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.matr.setRowCount(2**self.qubitscount.value())
        self.matr.setColumnCount(2**self.qubitscount.value())
        for r in range(self.matr.rowCount()):
            for c in range(self.matr.columnCount()):
                self.matr.setItem(r,c,QTableWidgetItem("0"))
        
        self.setLayout(layout)
        layout.addLayout(left)
        layout.addLayout(right)
        right.addWidget(self.matr)
        left.addWidget(self.name)
        left.addWidget(self.qubitscount)
        left.addWidget(self.multiplier)
        left.addWidget(self.img_chooser)
        left.addWidget(self.assocs)
        left.addWidget(self.saveG)   
     

class OptionsPopup(QWidget):
    """Responsible for presenting the user with tools to change accessibility settings"""

    def __init__(self,f,col):
        """Declares and initalises the accessibility options
        parameters:
            f (String): name of font family
            col (String): name of current highlight colour"""
        super().__init__()
        layout = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()
        
        self.font_size_wheel = QSpinBox()
        self.font_size_wheel.setValue(f.pointSize())
        self.font_size_wheel.setMinimum(5)

        self.setWindowTitle("Options menu")
        
        self.font_combo = QComboBox()
        for font in QFontDatabase().families():
            self.font_combo.addItem(font)
        self.font_combo.setCurrentText(f.family())
        
        self.colour_picker = QColorDialog()
        self.colour=(QColor(col))
        
        self.colour_picker_button = QPushButton()
        self.colour_picker_button.pressed.connect(self.update_col)
        self.colour_picker_button.setStyleSheet("background-color: {}".format(col))
        
        self.save_options = QPushButton("Save Options")
        self.setWindowTitle("Accessibility Options")

        self.setLayout(layout)
        layout.addLayout(left)
        layout.addLayout(right)
        
        left.addWidget(self.font_combo)
        left.addWidget(self.font_size_wheel)
        left.addWidget(self.colour_picker_button)

        left.addWidget(self.save_options)

    def update_col(self):
            """Updates the colour of the icon given the chosen colour"""

            self.colour = self.colour_picker.getColor()
            if self.colour.isValid():
                self.colour_picker_button.setStyleSheet("background-color: {}".format(self.colour.name()))

class GateInfoPopup(NewGatePopup):
    """Responsible for presenting the user with information relating to the gate specified"""

    def __init__(self,gate):
        """Inherits from NewGatePopup and initialises the fields with the gates values
        parameters:
            gate (Gate): reference to the gate objects"""
        super().__init__()
        self.gate = gate
        self.setWindowTitle("Gate editor")

        if(gate!=None):

            self.name.setText(gate.get_name())
            self.qubitscount.setValue(gate.get_qubits())
            self.name.setEnabled(False)

            self.qubitscount.setEnabled(False)

            self.multiplier.setText("1")
            self.multiplier.setEnabled(False)

            self.img_chooser.setEnabled(False)
            self.img_chooser.setText("")
            if(gate.get_icon()!=None):
                self.img_chooser.setIcon(QIcon(gate.get_icon()))
            else:
                self.img_chooser.setText("No Image")

            self.matr.setRowCount(2**self.qubitscount.value())
            self.matr.setColumnCount(2**self.qubitscount.value())
            self.matr.setEditTriggers(QTableWidget.NoEditTriggers)

            self.assocs.setColumnCount(1)

            if(isinstance(gate,ParamGate)):
                ps = gate.get_params()
                P = len(ps)
                self.assocs.setRowCount(P)
                self.assocs.setItem(0,0,QTableWidgetItem("holder"))
                i = 0
                for p in ps:
                    self.assocs.setVerticalHeaderItem(i,QTableWidgetItem(p))
                    self.assocs.setItem(0,i,QTableWidgetItem(str(ps[p])))
                    i = i + 1

            m = gate.get_matr()
            for i in range(len(m)):
                for j in range(len(m[i])):
                    self.matr.setItem(i,j,QTableWidgetItem(str(m[i][j])))
 
class CodeView(QWidget):
    """Responsible for presenting the user with an interface to view and generated edit the code """

    moments = -1
    curLang = ""
    
    def __init__(self):
        """Declares and initialises the code box, quantum solution chooser and run button"""
        super().__init__() 
        
        self.vboxRoot = QVBoxLayout()

        self.lang_sel = QComboBox()

        self.code_box = QPlainTextEdit()

        self.update_but = QPushButton("Generate")

        self.vboxRoot.addWidget(self.lang_sel)
        self.vboxRoot.addWidget(self.code_box)
        self.vboxRoot.addWidget(self.update_but)

        self.setLayout(self.vboxRoot)

    def reset_code(self,code,disp=0):
        """Empties the entry in the code box and then inserts the specified code
        parameters:
            code (String): code to insert into the code box"""
        self.code_box.clear()
        editor = self.code_box.textCursor()
        editor.select(QTextCursor.Document)
        self.code_box.setPlainText(editor.document().toPlainText())
        editor.movePosition(QTextCursor.Start)
        editor.insertHtml(format(code))
        maximum_scroll_value = self.code_box.verticalScrollBar().maximum()
        try:
            self.code_box.verticalScrollBar().setValue((disp/maximum_scroll_value) * 6)
        except:
            pass



                 
               