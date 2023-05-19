import view
import model
from PyQt5.QtGui import QFont,QIcon,QColor,QImageReader
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import *
import numpy as np
import gate
import ast
import math
import re
import logging
import copy
from cirq import *

class MainController():
    """Controls the view class by querying the model and updating the view"""

    
    def __init__(self):
        """intialises the controller, this includes establishing the mappings from each package to the model and the creation of model and view classes"""
        
        #init logging
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', filename='controller.log')

        #init model
        self.model = model.MainModel()
        
        self.langs = ["Cirq","Qiskit"]

        self.reg_count = self.model.reg_count

        #model to code mapping
        self.circn="circuit"
        self.qubitsn="qubits"     
        self.classicn = "classic"
        self.unitgen = "{}=np.array({})"
        self.custom_gates = []
        self.controlled_gates = []
        self.additional_imports = []
        
        self.model_to_cirq={}
        self.model_to_cirq["import"]=["from cirq import *","import numpy as np"]
        self.model_to_cirq["qub"]="{} = LineQubit.range({num})"
        self.model_to_cirq["circ"]="{} = Circuit()"
        self.model_to_cirq["gateparam"] = "{}[{}]"
        self.model_to_cirq["newgate"]="{n} = MatrixGate({matr},name=\"{n}\")"
        self.model_to_cirq["controlledgate"]="{}=ControlledGate({})"
        self.model_to_cirq["gate"]="{}.append({}({}))"
        self.model_to_cirq["paramgate"] ="{}.append({}({}))"
        self.model_to_cirq["Hadamard"]="H"
        self.model_to_cirq["Pauli_X"]="X"
        self.model_to_cirq["Pauli_Y"]="Y"
        self.model_to_cirq["Pauli_Z"]="Z"
        self.model_to_cirq["Controlled_X"]="CNOT"
        self.model_to_cirq["Controlled_Z"]="CZ"
        self.model_to_cirq["Swap"]="SWAP"
        self.model_to_cirq["T"]="T"
        self.model_to_cirq["Ry"]="ry"
        self.model_to_cirq["Measure"]="measure"
        self.model_to_cirq["Reset"]="reset"

        #model to qiskit
        self.model_to_qiskit={}
        self.model_to_qiskit["import"]=["import qiskit","from qiskit.extensions import UnitaryGate","import qiskit.circuit.library as qcl","import numpy as np"]
        self.model_to_qiskit["qub"]="{} = qiskit.QuantumRegister({num},'q') <br>{classicn} = qiskit.ClassicalRegister({num}, 'c')"
        self.model_to_qiskit["circ"]="{} = qiskit.QuantumCircuit({qubs},{classicn})"
        self.model_to_qiskit["gateparam"] = "{}[{}]"
        self.model_to_qiskit["newgate"]="{n} = UnitaryGate({matr}) <br>{n}.name = \"{n}\""
        self.model_to_qiskit["controlledgate"]="{}={}.control(1)"
        self.model_to_qiskit["gate"]="{}.append({},[{}])"
        self.model_to_qiskit["paramgate"] ="{}.append({},[{}])"
        self.model_to_qiskit["Hadamard"]="qcl.HGate()"
        self.model_to_qiskit["Pauli_X"]="qcl.XGate()"
        self.model_to_qiskit["Pauli_Y"]="qcl.YGate()"
        self.model_to_qiskit["Pauli_Z"]="qcl.ZGate()"
        self.model_to_qiskit["Swap"]="qcl.SWAPGate()"
        self.model_to_qiskit["Controlled_X"]="qcl.CXGate()"
        self.model_to_qiskit["Controlled_Z"]="qcl.CZGate()"
        self.model_to_qiskit["Ry"]="qcl.RYGate"
        self.model_to_qiskit["Measure"]="qcl.Measure()"
        self.model_to_qiskit["Reset"]="qcl.Reset()"

        self.composer_to_qiskit = {}
        self.composer_to_qiskit["h"]="HGate"
        self.composer_to_qiskit["x"]="XGate"
        self.composer_to_qiskit["y"]="YGate"
        self.composer_to_qiskit["z"]="ZGate"
        self.composer_to_qiskit["swap"]="SWAPGate"
        self.composer_to_qiskit["cx"]="CXGate"
        self.composer_to_qiskit["cz"]="CZGate"
        self.composer_to_qiskit["ry"]="RYGate"
        self.composer_to_qiskit["measure"]="Measure"
        self.composer_to_qiskit["reset"]="Reset"
        
        #init main view
        self.mv = view.MainWindow()
        
        self.mv.toolbar.actionTriggered.connect(self.toolbar_interact)
        self.mv.dv.qgate_list_widget.itemSelectionChanged.connect(self.update_prev_matr)
        self.update_prev_matr()

        #init code view
        self.cur_lang = "Cirq"
        self.code = {}
        self.code["body"]=[None for x in range(self.model.hidden_lim*self.reg_count)]
        self.code["custom"]=[]
        self.code["controlled"]=[]

        self.code_trace = {}

        self.mv.cv.lang_sel.currentTextChanged.connect(self.lang_sel_changed)
        self.mv.cv.update_but.pressed.connect(self.runpressed)

        for l in self.langs:
            self.mv.cv.lang_sel.addItem(l)

        #init diagram view

        
        for g in self.model.operations:
            try:
                ico = QIcon(self.model.operations[g].get_icon())
            except:
                self.mv.dv.qgate_list_widget.addItem(QListWidgetItem(self.model.operations[g].get_name()))
            else:
                self.mv.dv.qgate_list_widget.addItem(QListWidgetItem(ico,self.model.operations[g].get_name()))


        self.mv.dv.qgate_list_widget.doubleClicked.connect(self.change_image)

        self.mv.dv.registers.setRowCount(self.model.reg_count)
        self.mv.dv.registers.setColumnCount(self.model.hidden_lim)
        ns = [str(i) for i in range(self.mv.dv.registers.rowCount())]
        self.mv.dv.registers.setVerticalHeaderLabels(ns)
        self.fsize = 12
        self.update_view_options("Arial",self.fsize,"yellow")
        self.last_pressed = (-1,-1)
        self.mv.dv.registers.cellPressed.connect(self.cell_pressed)
        self.mv.dv.registers.currentCellChanged.connect(self.cur_cell_changed)
        self.mv.dv.registers.cellDoubleClicked.connect(self.cell_double_pressed)
        self.mv.dv.registers.dropEvent = self.drop_event_on_table

        # removed due to effect on performance
        # for r in [(x, y) for x in range(self.model.hidden_lim) for y in range(self.model.reg_count)]:
        #     icon = QIcon("imgs/placeholder.png")
        #     iconItem = QLabel()
        #     iconItem.setPixmap(icon.pixmap(icon.actualSize(QSize(20 * self.fsize, 20 * self.fsize))))
        #     iconItem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #     self.mv.dv.registers.setCellWidget(r[1], r[0], iconItem)
        
        
        self.mv.dv.qgate_list_widget.dropEvent = self.drop_event_on_gate_list  

        self.maths_whitelist = ["arccos","cos","sin","pi","j","exp","math"]

    def update_prev_matr(self):
        """updates the preview matrix to the selected gate in qgate_list_widget"""
        try:
            target = self.mv.dv.qgate_list_widget.selectedItems()[0]        
            matr = (self.model.operations[target.text()]).get_matr()
            self.mv.dv.matrix_preview.setEnabled(True)
        except:
            
            matr = [[0,0],
                    [0,0]]

        if(len(matr)==2 and sum(abs(x) for x in matr[0]) == 0 and sum(abs(x) for x in matr[1]) == 0):
            self.mv.dv.matrix_preview.setEnabled(False)
        else:
            self.mv.dv.matrix_preview.setEnabled(True)

        self.mv.dv.matrix_preview.setRowCount(len(matr))
        self.mv.dv.matrix_preview.setColumnCount(len(matr[0]))
        x = 0
        y = 0
        
        for i in range(len(matr)):            
            for j in range(len(matr[i])):
                titem = QTableWidgetItem(str(round(matr[i][j],3)))
                titem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.mv.dv.matrix_preview.setItem(i,j,titem)
                y = y + 1
            x = x + 1
        self.mv.dv.matrix_preview.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.mv.dv.matrix_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def run(self):
        """launches the main window"""
        self.mv.showMaximized()

    def runpressed(self):
        """triggers the conversion of custom code in the code box to the model"""
        self.code_to_model(self.mv.cv.code_box.toPlainText())        

    def toolbar_interact(self,tool):
        """handles the actions for each of the option buttons
        
        
        paramaters:
            tool (String): the title of the button"""
        
        if(tool.text()=="Add_qubit"):
            
            self.add_qub()
     
        elif(tool.text()=="Remove_qubit"):
            
            row_empty = True
            for i in range(self.model.hidden_lim):
                if(self.model.get_entry_at(i,self.model.reg_count-1) is not None):
                    row_empty = False
            if(row_empty):
                self.remove_qub()
            else:
                self.mv.error_popup("Remove entries from this qubit first!")

        elif(tool.text()=="New_gate"):

            self.mv.on_click_newGate()
            self.mv.window.qubitscount.valueChanged.connect(self.update_cust_q_no)
            self.mv.window.saveG.clicked.connect(self.init_custom_gate)
            self.mv.window.matr.cellChanged.connect(self.cast_cell_entry)
            self.mv.window.img_chooser.pressed.connect(self.load_image)

        elif(tool.text()=="Reset"):

            self.last_pressed = None
            self.reset_circuit()

        elif(tool.text()=="View_options"):

            self.mv.on_click_options(self.font,self.highlight_colour)
            self.mv.window.save_options.clicked.connect(self.init_view_options)

        elif(tool.text()=="Load"):

            logging.info("load pressed")
            try:
                self.mv.load_file()
            except:
                logging.info("failed to load file")

        elif(tool.text()=="Save"):

            logging.info("save pressed")

            try:
                self.mv.save_file()
            except:
                logging.info("failed to save")
    
    def change_image(self):
        """Allows the user to change the image of a gate"""
        sel =  QFileDialog.getOpenFileName()
        reader = QImageReader(sel[0])
        if(reader.canRead()):
            self.selected_img = sel[0]
            targ = (self.mv.dv.qgate_list_widget.selectedItems()[0])
            coords_to_names = {c: n.get_name() for c,n  in self.code_trace.items()}
            to_update = []
            for k in coords_to_names:
                if(coords_to_names[k] == targ.text()):
                    to_update.append(k)
            self.model.update_image(targ.text(),self.selected_img,to_update)
            targ.setIcon(QIcon(self.selected_img))
            self.respond_to_model(to_update)
        else:
            self.mv.error_popup("Must be a valid image file")

    def load_image(self):
        """Allows the user to load a file of text into the code box"""
        sel = QFileDialog.getOpenFileName(self.mv.window, 'Load File')
        reader = QImageReader(sel[0])
        if(reader.canRead()):
            self.selected_img = sel[0]
            self.mv.window.img_chooser.setIcon(QIcon(self.selected_img))
        else:
            self.mv.error_popup("Must be a valid image file")

    def update_cust_q_no(self):
        """updates the size of the custom gate matrix given the current value"""
        val =  self.mv.window.qubitscount.value()
        self.mv.window.matr.setRowCount(2**val)
        self.mv.window.matr.setColumnCount(2**val)

    def init_custom_gate(self):
        """initialises the fields in a fresh custom gate window"""
        
        R = self.mv.window.matr.rowCount()
        C = self.mv.window.matr.columnCount()

        matrix = np.zeros((R,C),dtype=complex)
        multi = exec(self.mv.window.multiplier.text())

        entries = {}

        for i in range(R):
            for j in range(C):
                try:
                    matrix[i,j]=complex(self.mv.window.matr.item(i,j).text())
                except:
                    matrix[i,j]=None
                    entries[(i,j)]=self.mv.window.matr.item(i,j).text()
        
        params = {}
        try:
            
            for i in range(self.mv.window.assocs.rowCount()):
                v = self.mv.window.assocs.verticalHeaderItem(i).text()
                
                params[self.mv.window.assocs.verticalHeaderItem(i).text()]=eval(self.mv.window.assocs.item(i,0).text())
        except:
            self.mv.error_popup("invalid value in parameter table")

        try:
            multi = eval(self.mv.window.multiplier.text())
        except:
            self.mv.error_popup("invalid value in mulitplier")            
        
        try:
            res = self.create_gate(self.mv.window.name.text(),self.mv.window.qubitscount.value(),multi,matrix,params,entries,img=self.selected_img)
        except:
            res = self.create_gate(self.mv.window.name.text(),self.mv.window.qubitscount.value(),multi,matrix,params,entries)

        if(res==True):
            self.mv.window.close()
        else:
            self.mv.error_popup(res)

    def init_view_options(self):
        """initialises the fields in the accessibility options window """
        
        self.update_view_options(self.mv.window.font_combo.currentText(),
              self.mv.window.font_size_wheel.value(),
              self.mv.window.colour)
        self.mv.window.close()
        
    def update_view_options(self,font,size,colour):
        """sets the accessibility options, program wide, according to the parameters
        
        parameters:
            font (String): name of desired PyQt5 supported font family
            size (int): desired font size
            colour (String): desired highlight colour"""

        try:
            self.highlight_colour=colour.name()
        except:
            try:
                self.highlight_colour=colour
            except:
                pass
        self.font=QFont(font,size)
        self.fsize = size
        self.mv.setFont(self.font)
        self.mv.dv.reset_column_sizes(self.fsize)
        targs = []
        for x in range(self.model.reg_count):
            for y in range(self.model.hidden_lim):
                targs.append((x,y))
        self.respond_to_model(targs)
        self.regen_code()

    def customise_gate(self,x,y):
        """customises the gate's underlying model values
        
        parameters:
            x (int): x value of gate in circuit
            y (int): y value of gate in circuit"""

        params = {}
        for i in range(self.mv.window.assocs.rowCount()):
            params[self.mv.window.assocs.verticalHeaderItem(i).text()]=eval(self.mv.window.assocs.item(i,0).text())
        self.model.customise_gate(x,y,params)
        self.regen_code()
        self.mv.window.close()

    def remove_qub(self):
        """attempts to remove one qubit and acts upon the model's response"""
        self.model.remove_qub()
        if(self.reg_count!=self.model.get_no_qubits()):
                self.reg_count=self.model.get_no_qubits()
                self.mv.dv.registers.removeRow(self.reg_count)
                self.update_code_qubits()  
                ns = [str(i) for i in range(self.mv.dv.registers.rowCount())]
                self.mv.dv.registers.setVerticalHeaderLabels(ns)  
        self.mv.dv.registers.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def add_qub(self):
        """attempts to add one qubit and acts upon the model's response"""
        self.model.add_qub()
        if(self.reg_count!=self.model.get_no_qubits()):
                self.reg_count=self.model.get_no_qubits()
                self.mv.dv.registers.insertRow(self.reg_count-1)
                self.update_code_qubits()
                ns = [str(i) for i in range(self.mv.dv.registers.rowCount())]
                self.mv.dv.registers.setVerticalHeaderLabels(ns)

    def add_moment(self):
        """adds a moment (another column) to the circuit"""
        self.model.add_time()
        self.mv.dv.registers.insertColumn(len(self.model.moments)-1)
    
    def cast_cell_entry(self,x,y):
        """casts entries into the custom gate matrix to appropriate data type"""
        
        entry = self.mv.window.matr.item(x, y).text()
        
        if entry is not None:
            vars = re.findall("[a-z,A-z]+",entry)  
            for w in self.maths_whitelist:
                if(vars.count(w)>0):
                    vars.remove(w)

            for i in range(self.mv.window.assocs.rowCount()):
                var = self.mv.window.assocs.verticalHeaderItem(i).text()
                if(vars.count(var)>0):
                    vars.remove(var)

            V = len(vars)
            for v in range(V):
                self.mv.window.assocs.insertRow(0)
                self.mv.window.assocs.setVerticalHeaderItem(0,QTableWidgetItem(vars[v]))
                self.mv.window.assocs.setItem(0,0,QTableWidgetItem("1"))

            marked = []
            for i in range(self.mv.window.assocs.rowCount()):
                header=self.mv.window.assocs.verticalHeaderItem(i)
                if(header.text()==""):
                    marked.append(i)
            for m in marked:
                self.mv.window.assocs.removeRow(m)
  
        else:
            entry = QTableWidgetItem()
            self.mv.window.matr.setItem(x, y, entry)
        
    def code_generator(self):
        """returns the dictionary of the current code to model mappings
        
        returns:
            (dictionary): code to model mapping of current quantum package"""
        if(self.cur_lang=="Qiskit"):
            return self.model_to_qiskit
        elif(self.cur_lang=="Cirq"):
            return self.model_to_cirq
    
    def gatecode_generator(self,x,y,item):
        """returns a line of code in the appropriate language corresponding to the item and it's position
        parameters:
            y (int): y value of item on registers
            x (int): x value of item on registers
            item (gate): the gate at x,y on the model
                
        returns:
            gc (str): generated code
                """
        gc = ""
        qubs = item.get_range_acc()
        mentionedAcc = item.get_range_mentioned()
        mentionedAccX = list(map(lambda d : y+d,mentionedAcc))
        gateParams=[]
        i = y+qubs[1]
        while (i<=y+qubs[0]):
            if(mentionedAccX.count(i)>0):
                gateParams.append(self.code_generator()["gateparam"].format(self.qubitsn,i))
            i = i + 1
        
        formattedGParams=self.list_to_str(gateParams)
        if(formattedGParams==""):
            formattedGParams=self.code_generator()["gateparam"].format(self.qubitsn,y)
        else:
            formattedGParams=formattedGParams+","+self.code_generator()["gateparam"].format(self.qubitsn,y)

        lgen = self.code_generator() #language generator
        if(isinstance(item,gate.ParamGate) and ("Controlled_" not in item.get_name())): #Prevents incorrect syntax for custom controlled parameterised gates
            paramParams = self.list_to_str(list(item.get_params().values()))
            gc = lgen["paramgate"].format(self.circn,"{}({})".format(lgen[item.get_name()],paramParams),formattedGParams)
        else:
            if(item.get_name()=="Measure" and self.cur_lang=="Qiskit"):
                gc = "{circn}.append(qcl.Measure(),[{formq}],[{formc}])".format(circn=self.circn,formq=formattedGParams,formc=("{}[{}]".format(self.classicn,i-1)))
            else:
                gc = lgen["gate"].format(self.circn,lgen[item.get_name()],formattedGParams)

        return gc
    
    def list_to_str(self,list):
        """converts a list of Strings to a formatted string for use in code
        parameters:
            list (String[]): a list of strings 
        
        returns:
            formattedGParams: """

        if(len(list)>0):
            formattedGParams=str(list[0])
            for i in range(1,len(list)):
                formattedGParams=formattedGParams+","+str(list[i])
            return formattedGParams
        else:
            return ""

    def regen_code(self,vars={}):
        """Regenerates all of the code in the selected language, informs the view and updates the code to operation trace"""
        formatted_code = "" #formatted code
        
        # Precursor code #

        self.prec_offset = 0
        self.code["imports"]=self.code_generator()["import"] + self.additional_imports
        for i in range(len(self.code["imports"])):
            formatted_code = formatted_code + self.code["imports"][i] + "<br>"
            self.prec_offset = self.prec_offset + 1
        
        self.code["qub"]=self.code_generator()["qub"].format(self.qubitsn,num=self.model.reg_count,classicn = self.classicn)
        formatted_code = formatted_code + self.code["qub"] + "<br>"
        self.prec_offset = self.prec_offset + 1
        
        self.code["circ"]=self.code_generator()["circ"].format(self.circn,qubs=self.qubitsn,classicn=self.classicn)
        formatted_code = formatted_code + self.code["circ"] + "<br>"
        self.prec_offset = self.prec_offset + 1

        formatted_code = formatted_code + "<br>"
        self.prec_offset = self.prec_offset + 1

        # Custom gate code

        self.cust_offset = 0
        self.code["custom"] = []
        if(vars=={}):
            for g in self.custom_gates:
                vars,unitv,gatev = self.get_custom_op_code(g)
                for v in vars:
                    self.code["custom"].append(v)
                self.code["custom"].append(unitv)
                self.code["custom"].append(gatev)
        else:
            for v in vars:
                self.code["custom"].append("{} = {}".format(v,vars[v]))

        for entry in self.code["custom"]:
            c = entry.count("<br>")
            formatted_code = formatted_code + entry + "<br>"
            self.cust_offset = self.cust_offset + c +1

        if(self.cust_offset>0):
            formatted_code = formatted_code + "<br>"
            self.cust_offset = self.cust_offset + 1

        # Controlled code #

        self.cont_offset = 0
        self.code["controlled"] = []
        for g in self.controlled_gates:
            var = self.get_controlled_op_code(g)
            self.code["controlled"].append(var)

        for entry in self.code["controlled"]:
            c = entry.count("<br>")
            formatted_code = formatted_code + entry + "<br>"
            self.cont_offset = self.cont_offset + c +1

        if(self.cont_offset>0):
            formatted_code = formatted_code + "<br>"
            self.cont_offset = self.cont_offset + 1

        # Body code #

        self.body_offset = 0

        try:
            model_ind = self.mv.dv.registers.selectedIndexes()[0]
            sel_coords = self.model.get_targ_coords(model_ind.column(),model_ind.row())
            logging.info("cell at ({},{}) selected".format(model_ind.row(),model_ind.column()))
        except:
            sel_coords=(-1,-1)
            logging.info("no cell currently selected")

        self.code["body"] = []
        self.code_trace = dict(sorted(self.code_trace.items(), key=lambda x: (x[0][0], x[0][1])))
        highlighted_ind = 0
        ind = 0
        for g in self.code_trace:
            ind = ind+1
            if(g==sel_coords):
                self.code["body"].append('<span style="background-color: {};">{}</span>'.format(self.highlight_colour,self.gatecode_generator(g[0],g[1],self.code_trace[g])))
                highlighted_ind = ind
            else:
                self.code["body"].append(self.gatecode_generator(g[0],g[1],self.code_trace[g]))
        
        for entry in self.code["body"]:
            if(entry is not None):
                formatted_code = formatted_code + entry + "<br>"
                self.body_offset = self.body_offset + 1  
        formatted_code = formatted_code + "<br>"
        self.body_offset = self.body_offset + 1
        print((self.cust_offset+self.cont_offset+self.prec_offset+highlighted_ind))
        self.mv.cv.reset_code(formatted_code,disp=(self.cust_offset+self.cont_offset+self.prec_offset+highlighted_ind))

    def update_code_qubits(self):
        """updates the code relating to the number of qubits currently in the circuit"""
        self.code["qub"]=(self.code_generator()["qub"]).format(self.qubitsn,num=self.reg_count,classicn=self.classicn)
        self.regen_code()

    def lang_sel_changed(self):
        """deals with a change in quantum solutions"""
        self.cur_lang = self.mv.cv.lang_sel.currentText()
        self.regen_code()

    def operation_added(self,x,y,item):
        """Handles the code generation for operations added to the circuit
            Parameters:
                x (int): x coordinate
                y (int): y coordinate
                item (Gate or Accessory): item which has been added to position at x,y (from model)
                """
        if(not isinstance(item,gate.Accessory)):
            self.code_trace[(y,x)]=item
        else:
            try:
                self.code_trace.pop((y,x))
            except:
                None
        
    def operation_removed(self,x,y):
        """Handles the code generation for operations removed from the circuit
            Parameters:
                x (int): x coordinate
                y (int): y coordinate
                """
        try:
            self.code_trace.pop((y,x))
        except:
            None

    def custom_op_created(self,created_gate):
        """handles the creation of a custom operation by adding to the various mappings of the controller
        parameters:
            created_gate (Gate): the custom gate object just created"""

        self.model_to_cirq[created_gate.get_name()]=created_gate.get_name()
        self.model_to_qiskit[created_gate.get_name()]=created_gate.get_name()
        self.custom_gates.append(created_gate)

        self.regen_code()

    def get_custom_op_code(self,cgate):
        """generates custom operation code given a gate object
        parameters:
            cgate (Gate): gate object for code generation
        returns:
            var (String[]): the code relating to the declaration of this gate 
            univtv (String[]): the code relating to the unitary matrix of this gate
            gatev (String): the code relating to the initialisation of this gate """

        var = []
        if(isinstance(cgate,gate.ParamGate)):
            for p in cgate.get_params():

                var.append("{} = {}".format(p,cgate.get_params()[p]))
        arr = str(cgate.get_matr_formatted()).replace("'","")
        name_m = cgate.get_name()+"_matr"
        unitv = self.unitgen.format(name_m,arr)
        gatev = self.code_generator()["newgate"].format(n=cgate.get_name(),matr=name_m)
        return var,unitv,gatev
    
    def get_controlled_op_code(self,cgate):
        """generates and returns the code associated with custom controlled gate operations
        paramters:
            cgate (Gate): gate object to have code generated
        returns:
            var (String): code related to the initialisation of the gate """
        params=""
        if(isinstance(cgate,gate.ParamGate)):
            params=self.list_to_str(list(cgate.get_params().values()))
            var=self.code_generator()["controlledgate"].format(self.code_generator()[cgate.get_name()],"{}({})".format(self.code_generator()[cgate.get_parent_gate().get_name()],format(params)))
        else:
            var=self.code_generator()["controlledgate"].format(self.code_generator()[cgate.get_name()],self.code_generator()[cgate.get_parent_gate().get_name()])
        return var       
        
    def drop_event_on_table(self, event):
        """handles drop events of the PyQt5 table representing the quantum circuit
        parameters:
            event (Event): holds information related to the drop event, it is generated by PyQt5
        """
        
        x = self.mv.dv.registers.indexAt(event.pos()).column()
        y = self.mv.dv.registers.indexAt(event.pos()).row()
        if(event.source()==self.mv.dv.qgate_list_widget):
            item = self.mv.dv.qgate_list_widget.selectedItems()[0]
            if(item.text()=="Control"):
                self.add_control(x,y)
            else:
                self.insert_gate(x,y,item.text())                     

        elif(event.source()==self.mv.dv.registers):
            try:
                item = self.mv.dv.registers.selectedItems()[0]                               
            except:
                logging.warning("no item selected on table")
            else:
                self.move_op(item.column(),item.row(),x,y)

        #event.source().clearSelection()

    def drop_event_on_gate_list(self,event):
        """handles events where an object is dropped on to the gates list 
        parameters:
            event (Event): holds information related to the event, this is generated by PyQt5"""
        try:
            item = self.mv.dv.registers.selectedItems()[0]
        except:
            logging.warning("No valid item selected to delete")
        else:
            x = item.column()
            y = item.row()
            self.remove_gate(x,y)            
            #event.source().clearSelection()

    def remove_gate(self,x,y): 
        """attempts removes the gate x,y on the quantum circuit
        paramters:
            x (int): x coordinate of the target cell
            y (int): y coordinate of the targeted cell"""
        self.mv.dv.registers.clearSelection()
        results = self.model.remove_gate(x,y) #returns affected coordinates
        self.respond_to_model(results)

    def insert_gate(self,x,y,item,item_obj=None):        
        """attempts to insert a gate at a specified x,y
        parameters:
            x (int): x coordinate of target
            y (int): y coordinate of target
            item (String): name of item dropped at target
            item_obj (Gate): reference to object"""
        self.mv.dv.registers.clearSelection()
        results = self.model.insert_gate(x,y,item,item_obj) #returns affected coordinates
        if(results==False):
            self.add_qub()
            self.add_moment()
            return self.insert_gate(x,y,item,item_obj) #returns affected coordinates
        else:
            self.respond_to_model(results)
            return results
            
    def create_gate(self,name,noqubs,multi,matr,params,entries,img=None):
        """attempts to create a gate and reacts to the results
        parameters:
            name (String): name of the new gate
            noqubs (int): number of qubits covered by the new gate
            multi (float): multiplier to the unitary matrix of the gate
            matr (String[]): matrix of the gate 
            params (Dictionary{String:float}): variable parameters and their specified values
            entries (Dictionary{(int,int):"String"}): coordinates and string value of each entry into the matrix
            """
        minors = []
        for i in range(1,noqubs):
            minors.append(i)
        res = self.model.create_gate(name,noqubs,matr,multi,minors,ps=params,es=entries,img=img)
        if(isinstance(res,str)):
            return res 
        else:
            try:
                ico = QIcon(res.get_icon())
            except:
                self.mv.dv.qgate_list_widget.addItem(QListWidgetItem(res.get_name()))
            else:
                self.mv.dv.qgate_list_widget.addItem(QListWidgetItem(ico,res.get_name()))
            self.custom_op_created(res)
            return True

    def respond_to_model(self,results):
        """responds to changes in the model by updating the view according to coordinates passed in
        parameters:
            results ((int,int)[]): a list of coordinates for the controller to apply updates to the view"""

        need_more_moments = False

        for r in results:
            mitem = self.model.get_entry_at(r[0],r[1]) #model item
            self.mv.dv.registers.removeCellWidget(r[1],r[0]) 
            if(mitem is not None):
                titem = QTableWidgetItem()
                titem.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                if(mitem.get_name()=="|"):
                    titem.setText("|")     
                    self.mv.dv.registers.setItem(r[1],r[0],titem)              
                elif(mitem.get_name()=="Control"):
                    titem.setText("●")
                    self.mv.dv.registers.setItem(r[1],r[0],titem)
                else:
                    if(mitem.get_icon()!=None):
                        icon = QIcon(mitem.get_icon())
                        iconItem = QLabel()
                        iconItem.setPixmap(icon.pixmap(icon.actualSize(QSize(4 * self.fsize, 4 * self.fsize))))
                        iconItem.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.mv.dv.registers.setCellWidget(r[1], r[0], iconItem)
                        titem.setText(mitem.get_name())
                        titem.setForeground(QColor(255, 255, 255))
                        self.mv.dv.registers.setItem(r[1],r[0],titem)
                    else:
                        titem.setText(mitem.get_name())
                        self.mv.dv.registers.removeCellWidget(r[1],r[0])
                        self.mv.dv.registers.setItem(r[1],r[0],titem)
                if(r[0] >= len(self.model.moments)-2):
                    need_more_moments = True
            else:
                self.mv.dv.registers.removeCellWidget(r[1],r[0])
                self.mv.dv.registers.setItem(r[1],r[0],QTableWidgetItem(None))
                # icon = QIcon("imgs/placeholder.png")
                # iconItem = QLabel()
                # iconItem.setPixmap(icon.pixmap(icon.actualSize(QSize(20 * self.fsize, 20 * self.fsize))))
                # iconItem.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # self.mv.dv.registers.setCellWidget(r[1], r[0], iconItem)

        if(need_more_moments):
            for i in range(int((len(self.model.moments)-1)/2)):
                self.add_moment()

        self.mv.dv.reset_column_sizes(self.fsize)
        
        toDel = []
        toAdd = []
        for r in results:
            if(self.model.get_entry_at(r[0],r[1])==None):
                toDel.append(r)
            else:
                toAdd.append(r)

        while(len(toDel)>0):
            temp = toDel.pop()
            self.operation_removed(temp[1],temp[0])     

        while(len(toAdd)>0):
            temp = toAdd.pop()
            g = self.model.get_entry_at(temp[0],temp[1])
            self.operation_added(temp[1],temp[0],g)             
              
        self.regen_code()

    def add_control(self,x,y,gate_obj=None,gate_name=None):
        """attempts to add a control to an existing gate and responds to the model's response
        parameters:
            x (int): x coordinate of targeted cell
            y (int): y coordainte of targeted cell
            gate_obj (Gate): reference to the gate object at the targeted cell
            gate_name (String): name of the gate at the targeted cell"""
        
        cgate,results = self.model.add_control(x,y,g_obj=gate_obj,g_n=gate_name)
        
        if(cgate is not None):
            self.model_to_cirq[cgate.get_name()]=cgate.get_name()
            self.model_to_qiskit[cgate.get_name()]=cgate.get_name()
            self.controlled_gates.append(cgate)
            self.mv.dv.qgate_list_widget.addItem(QListWidgetItem(cgate.get_name()))
        self.respond_to_model(results)

    def move_op(self,x1,y1,x2,y2):
        """attempts to move an operation given old and new coordinates"""
        self.mv.dv.registers.clearSelection()
        results = self.model.move_gate(x1,y1,x2,y2)
        self.respond_to_model(results)
        
    def reset_circuit(self):
        """resets the circuit starting with each of the adjustable values of the model and working through to variables in the controller and then finally updating the view according to these changes"""
        self.model.reset()
        self.circn="circuit"
        self.qubitsn="qubits"     
        self.classicn = "classic"
        self.mv.dv.registers.clear()
        self.mv.dv.qgate_list_widget.clear()
        self.mv.dv.registers.setColumnCount(0)
        self.mv.dv.registers.setRowCount(0)
        self.mv.dv.registers.setColumnCount(self.model.hidden_lim)
        self.mv.dv.registers.setRowCount(self.model.reg_count)
        ns = [str(i) for i in range(self.mv.dv.registers.rowCount())]
        self.mv.dv.registers.setVerticalHeaderLabels(ns)
        # for r in [(x, y) for x in range(self.model.hidden_lim) for y in range(self.model.reg_count)]:
        #     icon = QIcon("imgs/placeholder.png")
        #     iconItem = QLabel()
        #     iconItem.setPixmap(icon.pixmap(icon.actualSize(QSize(20 * self.fsize, 20 * self.fsize))))
        #     iconItem.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #     self.mv.dv.registers.setCellWidget(r[1], r[0], iconItem)
        for g in self.model.operations:
            try:
                ico = QIcon(self.model.operations[g].get_icon())
            except:
                self.mv.dv.qgate_list_widget.addItem(QListWidgetItem(self.model.operations[g].get_name()))
            else:
                self.mv.dv.qgate_list_widget.addItem(QListWidgetItem(ico,self.model.operations[g].get_name()))
        self.code = {}
        self.code["body"]=[None for x in range(self.model.hidden_lim*self.reg_count)]
        self.code["custom"]=[]
        self.code["controlled"]=[]
        self.controlled_gates = []
        self.custom_gates = []
        self.additional_imports = []
        self.code_trace = {}
        self.regen_code()

    def cur_cell_changed(self,y1,x1,y2,x2):
        """Keeps track of the previous and current cell selected"""
        self.mv.dv.registers.removeCellWidget(y1,x1)
        try:
            self.respond_to_model([(x2,y2)])
        except:
            logging.info("{} failed to update".format((x2,y2)))
        self.last_pressed = (x1,y1)

    def cell_pressed(self,x,y):
        """handles event where user presses a cell on the table"""
        if(self.last_pressed[1]==x and self.last_pressed[0]==y):
            self.mv.dv.registers.removeCellWidget(x,y)
        self.regen_code()

    def cell_double_pressed(self,x,y):
        """handles event where user double presses on a cell on the table
        parameters:
            x (int): x coordinate of cell pressed
            y (int): y coordinate of cell pressed"""
        res=self.model.get_targ_coords(y,x)
        if(self.model.get_entry_at(res[0],res[1]) is not None):
            self.mv.on_click_editGate(self.model.get_entry_at(res[0],res[1]))
            self.mv.window.saveG.clicked.connect(lambda: self.customise_gate(res[0],res[1]))
        
    def code_to_model(self,c):   
        """makes a best effort attempt to interpret code provided, the function takes a walk through each of the nodes on the abstract syntax tree of the parameter and updates the model which is informed by extensive querying""" 
        tree = ast.parse(c)
        local_vars = {}
        self.reset_circuit()
         
        if (self.cur_lang=="Cirq"):
            
            for node in ast.walk(tree):
                
                if isinstance(node, ast.Import): 
                    try:
                        nams = []
                        for n in node.names:
                            if(n.asname!=None):
                                i = "import {} as {}".format(n.name,n.asname)
                                if(not (i in self.model_to_cirq["import"])):
                                    nams.append(i)
                            else:
                                i = "import {}".format(n.name)
                                if(not (i in self.model_to_cirq["import"])):
                                    nams.append(i)
                        
                        for imp in nams:
                            self.additional_imports.append(imp)
                    except:
                        logging.error("invalid import")

                elif isinstance(node,ast.ImportFrom):
                    
                    try:
                        nams = []
                        for n in node.names:
                            nams.append(n.name)
                        
                        i = "from {} import {}".format(node.module,self.list_to_str(nams))
                        if(not (i in self.model_to_cirq["import"])):
                            self.additional_imports.append(i)
                    except:
                        logging.error("invalid import from")
                    
                elif isinstance(node, ast.Assign):

                    name = []
                    for n in node.targets:
                        name.append(n.id)
                    if(name == []):
                        break

                    try:
                        const = node.value.value
                        if isinstance(const, int):
                            n = node.targets[0].id
                            code = "{} = {}".format(n, const)
                            exec(code,globals(),local_vars)
                        else:
                            raise Exception
                    except:
                        logging.info("Assign not constant")
                    else:
                        logging.info("assigned constant")
                        continue
                                         
                    #check for valid instantiation of qubits and circuit
                    try:
                        func = node.value.func.id
                        if (func=="Circuit"):
                            self.circn = name[0]
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        logging.info("Assigned circuit")
                        continue

                    try:
                        func = node.value.func.value.id
                        qubs = int(node.value.args[0].value)
                        if (func=="LineQubit"):
                            self.qubitsn = name[0]
                            for x in range(self.reg_count):
                                self.remove_qub()
                            for q in range(self.reg_count,qubs):
                                self.add_qub()
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        logging.info("Assigned qubits")
                        continue

                    #check for matrix
                    try:
                        if(node.value.func.attr == 'array'):
                            matr_name = node.targets[0].id
                            matr = ast.unparse(node.value)
                            local_vars[matr_name] = matr
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        continue

                    #check for controlled gates
                    try:
                        try:
                            func = node.value.func.id
                            n = node.value.args[0].id
                            
                        except:
                            logging.info("not an unparameterised controlled gate")
                        try:
                            func = node.value.func.id
                            n = node.value.args[0].func.id
                            params = [] 
                            for p in node.value.args[0].args:
                                params.append(p.value)
                        except:
                            logging.info("not a parametersied controlled gate")
                        
                        for long in list(self.model_to_cirq.keys()): 
                            try:
                                if(((self.model_to_cirq[long]).replace("{}","")).replace("()","")==n):
                                    n=long
                            except:
                                if(self.model_to_cirq[long]==n):
                                    n=long
                        
                        if (func=="ControlledGate"):
                            
                            nitem = copy.deepcopy(self.model.operations[n])
                            i = 0
                            
                            if(nitem.parent == None and isinstance(nitem,gate.ParamGate)):
                                params = [] 
                                for p in node.value.args[0].args:
                                    params.append(p.value)
                                for k in (nitem.get_params()):
                                    nitem.get_params()[k]=params[i]
                                    i = i + 1

                            self.add_control(-1,-1,gate_obj=nitem,gate_name=name[0])
                        else:
                            raise Exception
                    except:
                        logging.info("Not a controlled gate")
                    else:
                        logging.info("controlled gate initilization")
                    
                    #check for custom gates
                    #self.create_gate(name[0],self.mv.window.qubitscount.value(),multi,matrix,ps=params,es=entries)
                    try:
                        vname = node.targets[0].id
                        matr_name = node.value.args[0].id
                        matr = eval(local_vars[node.value.args[0].id],globals(),local_vars)
                        nam = node.value.keywords[0].value.value
                        qubs = int(math.log2(math.sqrt(len(matr)*len(matr))))
                        
                        ps = {}
                        
                        mcopy = local_vars[node.value.args[0].id]
                        
                        temp = mcopy
                        for key in local_vars:
                            temp = mcopy.replace(key,"\"{}\"".format(key))
                            if(temp != mcopy):
                                ps[key]=local_vars[key]
                                mcopy = temp
                            else:
                                temp = mcopy
                        
                        local_vars["np"]=np
                        local_vars["math"]=math
                        mcopy = eval(local_vars[node.value.args[0].id],local_vars,globals())

                        entries = []
                        cur_str = ""
                        reading = False
                        for l in local_vars[node.value.args[0].id]:

                            if(l=="["):
                                entries.append(cur_str)
                                cur_str = ""
                                reading = True
                            elif(l==","):
                                entries.append(cur_str)
                                cur_str = ""
                            elif(l=="]"):
                                entries.append(cur_str)
                                cur_str = ""
                                reading = False
                                
                            if(reading):
                                cur_str += l
                        
                        reading1 = list(map(lambda x: x.replace("[",""),entries))
                        reading2 = list(map(lambda x: x.replace(",",""),reading1))
                        reading3 = list(filter(lambda x: len(x)!=0,reading2))
                        reading3 = np.array(reading3)
                        orig = reading3.reshape(len(matr),len(matr))

                        es = {}
                        if(len(ps)>0):
                            i = 0
                            for x in mcopy:
                                j = 0
                                for y in x:
                                    try:
                                        complex(orig[i,j])
                                    except:
                                        es[(i,j)]=orig[i,j]
                                        matr[i,j] = None
                                    j = j + 1
                                i = i + 1                       

                        local_vars[vname]=ast.unparse(node.value)
                        local_vars.pop("np")
                        local_vars.pop("math")
                        local_vars.pop("__builtins__")                        
                        self.create_gate(vname,qubs,1,matr,ps,es)               
                    except Exception as e:
                        try:
                            local_vars.pop("np")
                            local_vars.pop("math")
                            local_vars.pop("__builtins__")
                        except:
                            pass
                        logging.info("not a custom gate dec")
                    else:
                        continue

                elif isinstance(node, ast.Expr):
                    
                    param=[]
                    g=None

                    try:
                        g = node.value.args[0].func.id
                        circuitname = node.value.func.value.id
                        action = node.value.func.attr
                    except Exception as e:
                        logging.error("invalid simple expression {}".format(ast.dump(node)))
                        logging.error("with following error {}".format(e))

                    try:
                        g = node.value.args[0].func.func.id
                        for p in node.value.args[0].func.args:
                            param.append(p.value)
                        circuitname = node.value.func.value.id
                        action = node.value.func.attr
                    except Exception as e:
                        logging.error("invalid parameterised expression {}".format(ast.dump(node)))
                        logging.error("with following error {}".format(e))
                    
                    try: 
                        reg = []
                        for r in node.value.args[0].args:
                            reg.append(r.slice.value)
                        
                        if ( (len(set(reg))) != (len(reg)) ):
                            raise Exception
                        
                        #model
                        x=self.model.hidden_lim-1
                        y=reg.pop()
                        reg.append(y)
                        item = None
                        for n in self.model_to_cirq:
                                try:
                                    if(((self.model_to_cirq[n]).replace("{}","")).replace("()","")==g):
                                        item=n
                                except:
                                    if(self.model_to_cirq[n]==g):
                                        item=n
                        
                        nitem = copy.deepcopy(self.model.operations[item])
                        
                        if(param != []):
                            i = 0
                            for k in (nitem.get_params()):
                                nitem.get_params()[k]=param[i]
                                i = i + 1
                        
                        i = 1
                        reg.reverse()
                        for a in nitem.get_acc():
                                a.set_dist(reg[i]-y)
                                i = i + 1
                        nitem.update_links()


                        self.insert_gate(x,y,item,item_obj=nitem)
                        
                    except Exception as e:
                        logging.error("invalid expression {}".format(ast.dump(node)))
                        logging.error("with following error {}".format(e))
        
        elif(self.cur_lang=="Qiskit"):

            for node in ast.walk(tree):
            
                if isinstance(node, ast.Import): 
                        try:
                            nams = []
                            for n in node.names:
                                if(n.asname!=None):
                                    i = "import {} as {}".format(n.name,n.asname)
                                    if(not (i in self.model_to_qiskit["import"])):
                                        nams.append(i)
                                else:
                                    i = "import {}".format(n.name)
                                    if(not (i in self.model_to_qiskit["import"])):
                                        nams.append(i)
                            
                            for imp in nams:
                                self.additional_imports.append(imp)
                        except:
                            logging.error("invalid import")
                
                elif isinstance(node,ast.ImportFrom):
                        
                        try:
                            nams = []
                            for n in node.names:
                                nams.append(n.name)
                            
                            i = "from {} import {}".format(node.module,self.list_to_str(nams))
                            if(not (i in self.model_to_qiskit["import"])):
                                self.additional_imports.append(i)
                        except:
                            logging.error("invalid import from")
                
                elif isinstance(node,ast.Assign):
                    
                    try:
                        name = []
                        for n in node.targets:
                            name.append(n.id)
                        if(name == []):
                            break
                    except:
                        try:
                            name = []
                            for n in node.targets:
                                name.append("{}.{}".format(n.value.id,n.attr))
                            if(name == []):
                                break
                        except:
                            pass
                        else:
                            logging.info("found names: {}".format(name))
                    else:
                        logging.info("found names: {}".format(name))

                    try:
                        const = node.value.value
                        if isinstance(const, int):
                            n = node.targets[0].id
                            code = "{} = {}".format(n, const)
                            exec(code,globals(),local_vars)
                        elif isinstance(const,str):
                            for n in name:
                                code = ("{} = {}".format(n, const))
                                local_vars[n] = '\"{}\"'.format(const)
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        logging.info("Assigned constant {} = {}".format(n,const))

                    try:
                        func = node.value.func.attr
                        if (func=="QuantumCircuit"):
                            self.circn = name[0]
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        logging.info("Assigned circuit name: {}".format(self.circn))

                    try:
                        func = node.value.func.attr
                        if (func=="ClassicalRegister"):
                            self.classicn = name[0]
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        logging.info("Assigned qubits with numbers: {}".format(qubs))

                    try:
                        func = node.value.func.attr
                        qubs = int(node.value.args[0].value)
                        if (func=="QuantumRegister"):
                            self.qubitsn = name[0]
                            for x in range(self.reg_count):
                                self.remove_qub()
                            for q in range(qubs):
                                self.add_qub()
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        logging.info("Assigned qubits with numbers: {}".format(qubs))



                    #check for matrix
                    try:
                        if(node.value.func.attr == "array"):
                            matr_name = node.targets[0].id
                            matr = ast.unparse(node.value)
                            local_vars[matr_name] = matr
                        else:
                            raise Exception
                    except:
                        pass
                    else:
                        logging.info("Assigned matrix with name: {}".format(matr_name))
 
                    #check for controlled gates
                    try:
                        try:
                            n = "qcl." + node.value.func.value.func.attr + "()"
                            if(not (n in self.model_to_qiskit.values())):
                                raise Exception                     
                        except:
                            #not an unparameterised controlled gate
                            pass
                        try:
                            n = "qcl." + node.value.func.value.func.attr
                            if(n in self.model_to_qiskit.values()):
                                params = [] 
                                for p in node.value.func.value.args:
                                    params.append(p.value)
                            else:
                                raise Exception 
                        except:
                            #not a parametersied controlled gate
                            pass

                        try: 
                            n = node.value.func.value.id
                            if(not (n in self.model_to_qiskit.values())):
                                raise Exception   
                        except:
                            #not an unparameterised custom gate
                            pass 

                        try: 
                            n = node.value.func.value.func.id       
                            if(n in self.model_to_qiskit.values()):
                                params = [] 
                                for p in node.value.func.value.args:
                                    params.append(p.value)
                            else:
                                raise Exception 
                        except:
                            #not an parameterised custom gate
                            pass 

                        for long in list(self.model_to_qiskit.keys()): 
                            try:
                                if(((self.model_to_qiskit[long]).replace("{}","")).replace("()","")==n):
                                    n=long
                            except:
                                if(self.model_to_qiskit[long]==n):
                                    n=long
                     
                        nitem = copy.deepcopy(self.model.operations[n])
                        i = 0
                        
                        if(nitem.parent == None and isinstance(nitem,gate.ParamGate)):
                            for k in (nitem.get_params()):
                                nitem.get_params()[k]=params[i]
                                i = i + 1
                        
                        self.add_control(-1,-1,gate_obj=nitem,gate_name=name[0])
                    except:
                        pass
                    else:
                        logging.info("Controlled gate declaration and initilization")

                    #check for custom gates
                    try:
                        vname = node.targets[0].id
                        matr_name = node.value.args[0].id
                        matr = eval(local_vars[matr_name],globals(),local_vars)
                        qubs = int(math.log2(math.sqrt(len(matr)*len(matr))))
                        
                        ps = {}
                        
                        mcopy = local_vars[matr_name]
                        
                        temp = mcopy
                        for key in local_vars:
                            temp = mcopy.replace(key,"\"{}\"".format(key))
                            if(temp != mcopy):
                                ps[key]=local_vars[key]
                                mcopy = temp
                            else:
                                temp = mcopy
                        
                        local_vars["np"]=np
                        local_vars["math"]=math
                        mcopy = eval(local_vars[matr_name],local_vars,globals())

                        entries = []
                        cur_str = ""
                        reading = False
                        for l in local_vars[matr_name]:

                            if(l=="["):
                                entries.append(cur_str)
                                cur_str = ""
                                reading = True
                            elif(l==","):
                                entries.append(cur_str)
                                cur_str = ""
                            elif(l=="]"):
                                entries.append(cur_str)
                                cur_str = ""
                                reading = False
                                
                            if(reading):
                                cur_str += l
                        
                        reading1 = list(map(lambda x: x.replace("[",""),entries))
                        reading2 = list(map(lambda x: x.replace(",",""),reading1))
                        reading3 = list(filter(lambda x: len(x)!=0,reading2))
                        reading3 = np.array(reading3)
                        orig = reading3.reshape(len(matr),len(matr))        

                        es = {}
                        if(len(ps)>0):
                            i = 0
                            for x in orig:
                                j = 0
                                for y in x:
                                    try:
                                        complex(orig[i,j])
                                    except:
                                        es[(i,j)]=orig[i,j]
                                        matr[i,j] = None
                                    j = j + 1
                                i = i + 1        
        

                        local_vars[vname]=ast.unparse(node.value)
                        local_vars.pop("np")
                        local_vars.pop("__builtins__")
                        local_vars.pop("math")
                        self.create_gate(vname,qubs,1,matr,ps,es)      
                              
                    except:
                        try:
                            local_vars.pop("np")
                            local_vars.pop("__builtins__")
                            local_vars.pop("math")
                        except:
                            pass
                        pass
                    else:
                        logging.info("Custom gate declaration: {}".format(vname))

                elif isinstance(node,ast.Expr):

                    #find name of gate
                    g = None
                    generated = False #toggled if expression is in generated style

                    try:
                        g = node.value.args[0].func.attr
                        if(g in self.maths_whitelist):
                            raise Exception
                    except:
                        pass
                    else:
                        generated = True

                    try:
                        g = node.value.args[0].id
                        if(g in self.maths_whitelist):
                            raise Exception
                    except:
                        pass
                    else:
                        generated = True

                    try:
                        g = node.value.args[0].func.id
                        if(g in self.maths_whitelist):
                            raise Exception
                    except:
                        pass  
                    else:
                        generated = True


                    #composer style
                    if(not generated):
                        try:
                            g = node.value.func.attr
                        except:
                            pass

                    #find parameters
                    param = []
                    try:
                        if(generated):
                            for v in node.value.args[0].args:
                                param.append(v.value)
                        else:
                            raise Exception
                    except:
                        pass

                    try: #composer style parameters
                        for q in node.value.args:
                            if(not isinstance(q,ast.Subscript)):
                                param.append((eval(ast.unparse(q),globals())))
                    except:
                        pass

                    #find qubits
                    qubs = []
                    try:
                        for a in node.value.args:
                            if(isinstance(a,ast.List)):
                                for q in a.elts:
                                    qubs.append(q.slice.value)          
                    except:
                        pass

                    try: #composer style qubits
                        for q in node.value.args:
                            if(isinstance(q,ast.Subscript)):
                                qubs.append(q.slice.value)
                    except:
                        pass
                    
                    try: 

                        if ( (len(set(qubs))) != (len(qubs)) and (g!="Measure" and g!="measure")):
                            raise Exception
                        #model
                        x=self.model.hidden_lim-1
                        if(g=="Measure" or g=="measure"):
                            qubs.reverse()
                        y=qubs.pop()
                        qubs.append(y)
                        qubs.reverse()
                        
                        item = None
                        if(not generated): #deals with composer here
                            for n in self.composer_to_qiskit:
                                if(g==n):
                                    g = self.composer_to_qiskit[n]
                        
                        for n in self.model_to_qiskit:
                                try:
                                    if(self.model_to_qiskit[n]=="qcl.{}()".format(g)):
                                        item=n
                                    elif(self.model_to_qiskit[n]=="qcl.{}".format(g)):
                                        item=n
                                    else:
                                        raise Exception
                                except:
                                    if(g==n):
                                        item=n
                        
                        
                        nitem = copy.deepcopy(self.model.operations[item])
                        
                        if(param != []):
                            i = 0
                            for k in (nitem.get_params()):
                                nitem.get_params()[k]=param[i]
                                i = i + 1
                        
                        i = 1
                        for a in nitem.get_acc():
                                a.set_dist(qubs[i]-y)
                                i = i + 1
                        nitem.update_links()


                        self.insert_gate(x,y,item,item_obj=nitem)

                    except Exception as e:
                        logging.error("invalid expression {}".format(ast.dump(node)))
                        logging.error("with following error {}".format(e))

        self.regen_code(vars=local_vars)