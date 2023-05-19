
import gate
import copy
import numpy as np
from math import *
from cirq import MatrixGate

class MainModel():
    """Models the quantum circuit, using the moments list to hold positional data about each entry"""
    
    reg_count = 4

    moments = []

    gates = {}

    #hidden limit of columns
    hidden_lim = 25

    def __init__(self):
        """Sets the model to default values"""
        self.reset()

    def reset(self):
        """Resets the parameters of model to their original values, includes resetting the gate entries"""
        #self.reg_count = 4
        self.hidden_lim = 25
        self.moments = np.array([[None for y in range(self.reg_count)] for x in range(self.hidden_lim)])

        self.operations = {}
       
        self.create_gate("Hadamard",1,np.array([[1,1],[1,-1]]),multi=sqrt(1/2),img="imgs/hadamard.png")
            
        self.create_gate("Pauli_X",1,np.array([[0,1],[1,0]]),img="imgs/paulix.png")
        
        self.create_gate("Controlled_X",2,np.array([[0,1],[1,0]],dtype=complex),img="imgs/controlledx.png")
        self.operations["Controlled_X"].add_control(gate.Accessory("Control",self.operations["Controlled_X"],1))

        self.create_gate("Controlled_Z",2,np.array([[1,0],[0,-1]],dtype=complex),img="imgs/controlledz.png")
        self.operations["Controlled_Z"].add_control(gate.Accessory("Control",self.operations["Controlled_X"],1))
        
        # self.operations["Toffoli"]=gate.Gate("Toffoli",3,np.array([[0,1],[1,0]],dtype=complex))
        # self.operations["Toffoli"].add_control(gate.Accessory("Control",self.operations["Toffoli"],1))
        # self.operations["Toffoli"].add_control(gate.Accessory("Control",self.operations["Toffoli"],2))

        self.create_gate("Swap",2,np.array([[1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]],dtype=complex),1,[1],img="imgs/Swap.png")

        # self.operations["Identity"]=gate.Gate("Identity",1,np.array([[0,1],[0,1]],dtype=complex))

        # self.operations["T"]=gate.Gate("T",1,np.array([[1,0],[0,1j*pi/4]],dtype=complex))

        # self.operations["S"]=gate.Gate("S",1,np.array([[1,0],[0,"1j"]],dtype=complex))

        self.create_gate("Pauli_Z",1,np.array([[1,0],[0,-1]],dtype=complex),img="imgs/pauliz.png")

        # self.operations["T Dagger"]=gate.Gate("T Dagger",1,np.array([[1,0],[0,exp((-1j*pi)/4)]],dtype=complex)) #conjugate transpose of T

        # self.operations["S Dagger"]=gate.Gate("S Dagger",1,np.array([[1,0],[0,-1j]],dtype=complex))

        # self.operations["P"]=gate.ParamGate({"lambda":pi/2},{(1,1):"exp(1j*lambda)"},"P",1,np.array([[1,0],[0,None]],dtype=complex)) #lambda = pi, pi/2, pi/4 is equivalent to Z,S,T

        # self.operations["Rz"]=gate.ParamGate({"theta":pi/2},{(0,0):"exp((-1j*theta)/2)",(1,1):"exp((1j*theta)/2)"},"S",1,np.array([[None,0],[0,None]],dtype=complex)) 

        # self.operations["Sx"]=gate.Gate("Sx",1,np.array([[0.5+0.5j, 0.5-0.5j],[0.5-0.5j, 0.5+0.5j]],dtype=complex))

        # self.operations["Sx Dagger"]=gate.Gate("Sx Dagger",1,np.array([[0.5-0.5j, 0.5+0.5j],[0.5+0.5j, 0.5-0.5j]],dtype=complex))
        
        self.create_gate("Pauli_Y",1,np.array([[0,1j],[-1j,0]],dtype=complex),img="imgs/pauliy.png")

        # self.operations["Rx"]=gate.ParamGate({"theta":pi/2},{(0,0):"cos(theta/2)",(1,0):"-1j*sin(theta/2)",(0,1):"-1j*sin(theta/2)",(1,1):"cos(theta/2)"},"Rx",1,np.array([[None,None],[None,None]],dtype=complex)) 

        self.operations["Ry"]=gate.ParamGate({"theta":pi/2},{(0,0):"cos(theta/2)",(1,0):"-sin(theta/2)",(0,1):"sin(theta/2)",(1,1):"cos(theta/2)"},"Ry",1,np.array([[None,None],[None,None]],dtype=complex),image="imgs/roty.png") 
        
        # self.create_gate("RXX",2,np.array([[None,0,0,None],[0,None,None,0],[0,None,None,0],[None,0,0,None]],dtype=complex),1,["B"],ps={"theta":pi/2},es={(0,0):"cos(theta/2)",(3,0):"-1j*sin(theta/2)",(1,1):"cos(theta/2)",(2,1):"-1j*sin(theta/2)",(1,2):"-1j*sin(theta/2)",(2,2):"cos(theta/2)",(0,3):"-1j*sin(theta/2)",(3,3):"cos(theta/2)"})

        # self.operations["U"]=gate.ParamGate({"theta":pi/2,"phi":pi/2,"lambda":pi/2},{(0,0):"cos(theta/2)",(1,0):"-exp(1j * lambda)*sin(theta/2)",(0,1):"exp(1j * phi)*sin(theta/2)",(1,1):"exp(1j *(phi + lambda))*cos(theta/2)"},"U",1,np.array([[None,None],[None,None]],dtype=complex)) 
        
        self.create_gate("Measure",1,[[0,0],[0,0]],img="imgs/measure.png") 
        self.create_gate("Reset",1,[[0,0],[0,0]],img="imgs/reset.png")        
        self.create_gate("Control",1,[[0,0],[0,0]],img="imgs/control.png")

    def add_qub(self):
        """Adds a qubit to the quantum circuit"""
        temp = [None for x in range(self.moments.shape[0])]
        self.moments = np.column_stack((self.moments,temp))
        self.reg_count = self.reg_count+1

    def remove_qub(self):
        """Removes a quantum circuit as long as there is at least 2"""
        if (self.reg_count >= 1):
            self.reg_count = self.reg_count - 1
            self.moments = np.delete(self.moments,self.reg_count,axis=1)    
     
    def add_time(self):
        """Adds a moment to the quantum circuit, represented by a column"""
        self.hidden_lim = self.hidden_lim+1
        temp = [None for x in range(self.moments.shape[1])]
        self.moments = np.row_stack((self.moments,temp))

    def get_no_qubits(self):
        """Accessor for reg_count
        returns:
            reg_count (int): number of registers"""
        return self.reg_count
    
    def create_gate(self,name,qubits,matrix,multi=1,minors=[],ps={},es={},par=None,img=None):
        """Creates a new gate given the parameters
        parameters:
            name (String): name of new gate
            qubits (int): number of qubits gate covers
            matrix (String[]): unitary matrix of gate
            multi (float): multiplier to the unitary matrix
            minors (String[]): names of the additioinal accessories
            ps (Dictionary{String:float}): parameters of the unitary matrix
            es (Dictionary{(int,int):String}): customisable entries into the matrix
            par (Gate): parent gate of this gate
            img (String): path to icon
        
        returns:
            gate (Gate): reference to the gate object"""

        matrix = matrix * multi

        if(name in self.operations):
            return "The gate cannot have the same name as another gate"
        
        if(not self.is_unitary(matrix)):
            return "The matrix must be unitary"
        
        if(name in ps):
            return "The name of the gate can't be the same as any of the parameters"
        
        if(name not in self.operations and self.is_unitary(matrix)):
            if(ps == {} and es == {}):
                self.operations[name]=(gate.Gate(name,qubits,matrix,parent=par,image=img)) 
            else:
                self.operations[name]=(gate.ParamGate(ps,es,name,qubits,matrix,parent=par,image=img)) 
            i = 1
            for m in minors:
                self.operations[name].add_acc(gate.Accessory(name+" input "+str(m),self.operations[name],i,mentioned=True,image=img))
                i = i + 1
            return self.operations[name]
        else:
            return False

    def is_unitary(self,matrix):
        """Determines if a matrix is unitary
        parameters:
            matrix (float): given matrix
        returns:
            result (Bool): is the matrix unitary?"""
        # try:
        #     MatrixGate(matrix)
        # except:
        #     return False
        # else:
        #     return True
        return True
    
    def update_image(self,g,path,updates):
        """Updates the image of an operation
        parameters:
            g (Gate): gate object to change
            path (str): path to icon
            updates ((int,int)[]): coordinates of any instance of this Gate on the registers"""
        self.operations[g].set_icon(path)
        for c in updates:
            self.moments[c[0],c[1]].set_icon(path)

    def customise_gate(self,x,y,params):
        """Customises a gate in the model according to the provided parameters
        parameters:
            x (int): x value of target in circuit
            y (int): y value of target in circuit 
            params (Dictionary{String:float}): updated parameters
        """
        target = self.moments[x,y]
        
        for p in params:
            target.get_params()[p]=params[p]
    
    def can_fit(self,x,y,target):
        """Determines if a gate can fit at a given entry in the quantum circuit
        parameters:
            x (int): x entry into circuit
            y (int): y entry into circuit
            target (Gate): gate object to be checked
        
        returns:
            result (Bool): can the gate fit at that location?"""
        coords = self.get_full_coords(x,y,target,True)
        return (len([x for x in coords if x[1] >= 0 and x[1] < self.reg_count]) == len(coords))

    def reachable(self,coords):
        """takes in all coordinates to the right of a gate and trims them to remove non-touching ones
        parameters:
            coords ((int,int)[]): set of coordinates to trim
        returns:
            fin ((int,int)[]): trimmed set of coordinates"""
        coords = sorted(coords)
        fin = [coords[0]]
        for i in range(1, len(coords)):
            x1, y1 = coords[i-1]
            x2, y2 = coords[i]
            if x2 - x1 <= 1 and y2 - y1 <= 1 and (x1,y1) in fin:
                fin.append((x2,y2))           
        return fin


    def insert_gate(self,x,y,name,gate_obj=None):
            """returns affected coordinates and changes the model depending on the situation.
            the gate can shift other gates, be shifted, fit perfectly or be rejected
            parameters:
                x (int): x position in circuit
                y (int): y position in circuit
                name (String): name of the gate to be inserted
                gate_obj (Gate): reference to object of gate to be inserted
            
            returns:
                coords ((int,int)[]): affected coordinates in the operation """

            coords = []
            if(gate_obj==None):
                gate_obj = copy.deepcopy(self.operations[name])

            if(self.can_fit(x,y,gate_obj)):
            
                first_available = self.find_cells_to_shift_to(x,y,gate_obj)

                if(first_available!=[]):

                    for c in first_available:
                        self.moments[c[0],c[1]]=first_available[c]
                        coords.append(c)
                    
                else:
                    coords.append((x,y))
                    displaced = []
                    displaced = self.find_coords_to_right(x,y,gate_obj,[])
                    disp = self.reachable(displaced)
                    disp.reverse()
                    temp = {}
                    for d in disp:
                        temp[(d[0],d[1])] = self.moments[d[0],d[1]]
                        self.moments[d[0],d[1]]=None
                        coords.append(d)
                        self.moments[d[0]+1,d[1]]=temp[(d[0],d[1])]
                        coords.append((d[0]+1,d[1]))
                    self.moments[x,y]=gate_obj
                    coords.append((x,y))

                    for a in gate_obj.get_acc():
                        self.moments[x,y+a.get_dist()]=a
                        coords.append((x,y+a.get_dist()))

                return coords
            else:
                return False

    def find_cells_to_shift_to(self,x,y,gate_obj):
        """Returns the coordinates that a gate could shift to by checking for empty cells to the left of a gate
        parameters:
            x (int): x position of gate in circuit
            y (int): y position of gate in circuit
            gate_obj (Gate): reference to the gate object in question
            
        return:
            coords ((int,int)[]): the coordinates to which the gate in question should shift to"""
        accrange = gate_obj.get_range_acc()
        acclist = (list(range(accrange[1],accrange[0])))
        acclist.append(accrange[0])
        yrange = list(set(map(lambda d: y+d, acclist)))
        locked = True
        current = (x,y)
        if(x==0):
            i = x
        else:
            i = x - 1
        while(i>=0 and locked):
            for j in yrange:
                if(self.moments[i,j] is not None):
                    locked = False
            if(locked):
                current=(i,y)
            i = i - 1

        empty = list(map(lambda b: self.moments[x,b] is None,yrange))

        if(current==(x,y) and not locked and empty.count(False)>0):
            return []
            
        coords = {}
        coords[(current[0],current[1])]=gate_obj
        yrange.remove(y)
        for a in gate_obj.get_acc():
            coords[(current[0],current[1]+a.get_dist())]=a
        
        return coords

    def find_coords_to_right(self,x,y,newgate,progress):
        """Recursively finds and returns any operation on the circuit to the right of x,y and it's associated coordinates
        parameters:
            x (int): x position of gate in question
            y (int): y position of gate in question
            newgate (Gate): reference to the gate in question
            progress ((int,int)[]): each coordinate already found
        
        return:
            progress ((int,int)[]): each coordinate found in the recursive process"""

        if(isinstance(newgate,gate.Gate) or isinstance(newgate,gate.ParamGate)):
            
            ys = list(map(lambda a: y+a.get_dist(),newgate.get_acc()))
            ys.append(y)
        
        
            for i in range(self.hidden_lim):
                for j in ys:
                    if(self.get_entry_at(x+i,j) is not None and (x+i,j) not in progress):
                        progress.append((x+i,j))
                        self.find_coords_to_right(x+i,j, self.get_entry_at(x+i,j), progress)

        elif(isinstance(newgate,gate.Accessory)):
            ncs = self.get_targ_coords(x,y)
            self.find_coords_to_right(ncs[0],ncs[1],self.get_entry_at(ncs[0],ncs[1]),progress)

        return progress
    
    def remove_gate(self,x,y):
        """Removes the gate from the circuit at the given coordinates
        parameters:
            x (int): x position of the gate to delete
            y (int): y position of the gate to delete
            
        return:
            coords ((int,int)[]): the affected coordinates in the operation"""
        
        coords = []
        item = self.moments[x,y]
        if(isinstance(item,gate.Accessory)):
            targC = self.get_targ_coords(x,y)
            return self.remove_gate(targC[0],targC[1])
        elif(item is None):
            return []
        else:
            displaced = self.find_coords_to_right(x,y,item,[])
            self.moments[x,y]=None
            coords.append((x,y))
            displaced.remove((x,y))
            for a in item.get_acc():
                self.moments[x,y+a.get_dist()]=None
                coords.append((x,y+a.get_dist()))
                displaced.remove((x,y+a.get_dist()))

            dispSorted = []
            for d in displaced:
                if(isinstance(self.moments[d[0],d[1]],gate.Gate) or isinstance(self.moments[d[0],d[1]],gate.ParamGate)):
                    dispSorted.append(d)

            dispSorted = (sorted(dispSorted))
            temp = {}
            for d in dispSorted:
                temp[d] = self.moments[d[0],d[1]]
                self.moments[d[0],d[1]]=None
                coords.append(d)

            for d in displaced:
                self.moments[d[0],d[1]]=None
                coords.append(d)

            for d in dispSorted:
                coords.append(self.insert_gate(d[0],d[1],temp[d].get_name(),gate_obj=temp[d]))
            
            coordsFin = []
            for e in coords:
                if(isinstance(e,list)):
                    while(len(e)>0):
                        coordsFin.append(e.pop())
                else:
                    coordsFin.append(e)
            
            return coordsFin
    
            return False

    def define_control(self,target,name,disp=[]):
        
        """Creates a new controlled version of a gate
        parameters:
            target (Gate): reference to the gate to add a control to
            name (String): name of the gate to add a control to
            disp (int[]): distances from the gate to add the controls
            
        returns:
            newg (Gate): reference to the new gate object"""

        for o in self.operations:
            if(o==name):
                return None

        if (disp==[]):
            disp = len(target.get_acc())+1
        
        if(isinstance(target,gate.ParamGate) and (target.parent == None)):

            self.create_gate(name,target.get_qubits()+1,np.array(target.get_matr()),ps=target.get_params(),es=tarF.getEntries(),par=target)
            
        else:
            self.create_gate(name,target.get_qubits()+1,np.array(target.get_matr()),par=target)
            
        
        for a in (target.get_acc()):
            #if(a.is_mentioned()):
                self.operations[name].add_acc(gate.Accessory(a.get_name(),name,a.get_dist(),image=a.get_icon())) 
        self.operations[name].add_control(gate.Accessory("Control",name,disp))  
        newg = self.operations[name]
        return newg
    
    def add_control(self,x,y,g_obj=None,g_n=None):
        """Creates and adds a control to gates upon request
        parameters:
            x (int): x position of the target gate
            y (int): y position of the target gate
            g_obj (Gate): reference to gate to be controlled
            g_n (String): name of the gate to be controlled
            
        return:
            gate (Gate): reference to the newly controlled gate 
            coords ((int,int)[]): coordinates affected by the operation"""
        if(x==-1 and y==-1 and g_obj!=None):
            newg = self.define_control(g_obj,g_n)
            return newg,[]
        else:
            target = self.moments[x,y]
            if((isinstance(target,gate.Gate) or isinstance(target,gate.ParamGate)) and (target.get_matr()!=[])):
            
                coords = []

                d = self.get_next_acc_space(x,y,target)
                if(d is not None):
                    newg = self.define_control(target,"Controlled_"+target.get_name(),disp=d)
                    if(newg is not None):
                        remove = self.remove_gate(x,y)
                        insert = self.insert_gate(x,y,newg.get_name(),newg)

                        for r in remove:
                            coords.append(r)

                        for i in insert:
                            coords.append(i)
                        
                        return newg,coords
                    else:
                        return None,[]
                else:
                    return None,[]
            elif(isinstance(target,gate.Accessory)):
                return self.add_control(x,self.get_targ_coords(x,y)[1])
            else:
                return None,[]

    def move_acc(self,x1,y1,x2,y2):
        """Moves accessory around circuit through removal and reinsertion
        returns:
            coords ((int,int)[]): affected coordinates of the opeartion"""
        item = self.moments[x1,y1]
        if(item is None):
            return []
        elif(isinstance(item,gate.Gate) or isinstance(item,gate.ParamGate)):
            return self.move_gate(x1,y1,x2,y2)
        elif(isinstance(item,gate.Accessory)):
            if(x1==x2 and (self.get_entry_at(x2,y2)==None or self.get_entry_at(x2,y2).get_name()=="|")):
                
                targC = self.get_targ_coords(x1,y1)
                targ = self.moments[targC[0],targC[1]]
                dtarg = copy.deepcopy(targ)
                orig = self.moments[x1,y1]
                disp = y2-targC[1]
                dtarg.rem_acc(self.moments[x1,y1])
                dtarg.add_acc(gate.Accessory(orig.get_name(),targ,disp,image=orig.get_icon()))

                coords = []
                
                remove = self.remove_gate(targC[0],targC[1])
                insert = self.insert_gate(targC[0],targC[1],dtarg.get_name(),dtarg)
                

                for r in remove:
                    coords.append(r)

                for i in insert:
                    coords.append(i)

                return coords
            else:
                return []
        else:
            return []

    def move_gate(self,x1,y1,x2,y2):
        """Moves gate around circuit through removal and reinsertion
        returns:
            coords ((int,int)[]): affected coordinates of the operation"""
        item = self.moments[x1,y1]
        if(item is None):
            return []
        elif(isinstance(item,gate.Accessory)):
            return self.move_acc(x1,y1,x2,y2)
        elif(isinstance(item,gate.Gate) or isinstance(item,gate.ParamGate)):

            coords = [(x1,y1),(x2,y2)]
            
            if(self.can_fit(x2,y2,item)):

                
                remove = self.remove_gate(x1,y1)
                insert = self.insert_gate(x2,y2,item.get_name(),item)

                for r in remove:
                    coords.append(r)

                for i in insert:
                    coords.append(i)
            return coords

    def get_entry_at(self,x,y):
        """Safely returns the entry at the given coordinates"""
        if(x < self.hidden_lim and y < self.reg_count):
            return self.moments[x,y]
        else:
            return None
    
    def get_next_acc_space(self,x,y,item):
        """Returns next available space for a control, preferring upwards
        parameters:
            x (int): x value of target gate
            y (int): y value of target gate 
            item: reference to the item in question
        
        return:
            targ (int): next closest distance for an accessory on the circuit and target """
        res = self.get_full_coords(x,y,item)
        if(len(res)==1):
            if(res[0][1]==0):
                return 1 
            elif(res[0][1]<self.reg_count):
                return -1                
        elif(len(res)>1):
            i = y
            targ = 0
            while(i>=0 and i<self.reg_count):
                if(res.count((x,i))==0):
                    return targ           
                else:
                    i = i + 1
                    targ = targ + 1            
            i = y
            targ = 0
            while(i>=0 and i<self.reg_count):
                    if(res.count((x,i))==0):
                        return targ               
                    else:
                        i = i - 1
                        targ = targ - 1            
        return None
            
    def get_targ_coords(self,x,y):
        """Returns the coordinates of the gate associated with this accessory
        parameters:
            x (int): x value of target accessory
            y (int): y value of target accessory 
        
        returns:
            coords ((int,int)): coordiates of the gate"""
        if(isinstance(self.get_entry_at(x,y),gate.Accessory)):
            acc = self.moments[x][y]
            return (x,y-acc.get_dist())
        else:
            return (x,y)

    def get_full_coords(self,x,y,item,includeOrig=True): 
        """Returns all of the coordinates associated with this operation 
        parameters:
            x (int): x value of target operation
            y (int): y value of target operation
            item (Gate): reference to the operation object
            includeOrig (Bool): should coords include the original coordinates?
        
        returns:
            coords ((int,int)[]): coordiates of the gate and accessories"""    
        hits = [acc for acc in item.get_acc()]
        hits = map(lambda acc: y+acc.get_dist(),hits)
        hits = [(x,accy) for accy in hits]
        if(includeOrig):
            hits = [(x,y)]+hits
        return hits

    def pretty_print_matr(self):
        """Pretty prints the circuit to stdout"""
        for i in range((self.reg_count)):
            for j in range((self.hidden_lim)):
                try:
                    print(self.moments[j][i].get_name(), end=' ')
                except:
                    print(None,end=' ')
            print()

        print("---")
