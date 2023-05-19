
import cirq
import copy
import numpy as np
import re
from math import *

class Gate():
    """Models a quantum gate"""
    
    def __init__(self,name,qubits,matrix,multi=1,parent=None,image=None):
        self.name = name
        self.qubits = qubits
        self.matrix = matrix
        self.accessories = []
        self.multi = multi
        self.parent = parent
        self.image = image
        
    def get_icon(self):
        """Attemps to return the image associated with this Gate"""
        return self.image
    
    def set_icon(self,path):
        """Mutator to icon path
        parameters:
            path (str): relative path to icon"""
        self.image = path
        
    def get_multi(self):
        """accessor to the multiplier
        returns:
            self.multiplier (float): mutliplier to the unitary matrix"""
        return self.multi

    def get_qubits(self):
        """Accessor to the number of qubits covered by this Gate
        returns:
            self.qubits(int): number of qubits covered by this"""
        return self.qubits
    
    def get_name(self):
        """Accessor to the name of this gate
        returns:
            self.name (String): name of this Gate"""
        return self.name

    def add_control(self,acc):
        """Adds a control and alter this Gates unitary matrix accordingly
        parameters:
            acc (Accessory): custom control accessory to add
        returns:
           [acc.get_dist()]+self.update_links() (int[]): new list of accessory distances"""
        m = list(filter(lambda x: x.is_mentioned(),self.accessories)) # me
        mto = (list(map(lambda x: x.get_dist(),m))) # more than once
        if mto.count(acc.get_dist()) == 0:
            self.accessories.append(acc)
            tempGate = cirq.MatrixGate(self.matrix)
            tempGate = tempGate.controlled()
            self.matrix = cirq.unitary(tempGate)
            return [acc.get_dist()]+self.update_links()
        
    def add_acc(self,acc):
        """Adds a custom accessory to this Gate
        parameters:
            acc (Gate): custom accessory to add
        returns:
            [acc.get_dist()]+self.update_links() (int[]): new list of accessory distances"""
        m = list(filter(lambda x: x.is_mentioned(),self.accessories)) # me
        mto = (list(map(lambda x: x.get_dist(),m))) # more than once
        if mto.count(acc.get_dist()) == 0:
            self.accessories.append(acc)
            return [acc.get_dist()]+self.update_links()

    def update_links(self):
            """Updates the Gate to have links to each of it's accessories
            returns:
                res (int[]): list of link's distances from this Gate"""
            toDel = []
            for x in self.accessories:
                if(x.get_name()=="|"):
                    toDel.append(x)
            self.accessories = [x for x in self.accessories if x not in toDel]
            r = list(range(self.get_range_acc()[1],self.get_range_acc()[0]))
            r = [x for x in r if x not in list(map(lambda y: y.get_dist(),self.accessories)) and x != 0]
            i = 0
            res = []
            while(i < len(r)):
                self.accessories.append(Accessory("|",self,r[i],False))
                res.append(r[i])
                i = i + 1
            return res
            
    def rem_acc(self,acc):
        """Removes a given accessory from the gate
        parameters:
            acc (Accessory): given accessory"""
        iss = []
        for i in range(len(self.accessories)):
            if(self.accessories[i].get_dist()==acc.get_dist()):
                iss.append(self.accessories[i])
        for a in iss:
            self.accessories.remove(a)

    def get_acc(self):
        """Accessor to the accessories of this gate
        returns:
            self.accessories (Accessory[]): list of this Gate's accessories"""
        return self.accessories
    
    def get_furthest_acc(self):
        """Accessor to the furthest accessory from this Gate
        returns:
            max (int): distance from the Gate"""
        max = 0
        for a in self.accessories:
            if a.get_dist() > max:
                max = a.get_dist()
        return max
    
    def get_range_acc(self):
        """Accessor to the range of accessories from highest to lowest
        returns:
            range (int[]): range of accessory distances"""
        range = [0,0]
        for a in self.accessories:
            if a.get_dist() > range[0]:
                range[0] = a.get_dist()
            elif a.get_dist() < range[1]:
                range[1] = a.get_dist()
        return range #where range[0] is max and range[1] is min
    
    def get_range_mentioned(self):
        """Returns the range of accessories which may be mentioned in code
        returns:
            range (int): distance of each of the accessories that may be mentioned in code"""
        range = []
        for a in self.accessories:
            if(a.is_mentioned()):
                range.append(a.get_dist())            
        return range #where range[0] is max and range[1] is min

    def get_matr(self):
        """Accessor to the unitary matrix of the Gate
        returns:
            self.matrix (float[]): unitary matrix of the Gate"""
        return self.matrix
    
    def get_matr_formatted(self):
        """Accessor to the unitary matrix in a Python list
        returns:
            self.matrix.tolist() (float[]): in order to manipulate it in Pythonic terms"""
        return self.matrix.tolist()

    def get_parent_gate(self):
        """Accessor to the parent Gate of this Gate
        returns:
            self.parent (Gate): parent Gate"""
        return self.parent

class ParamGate(Gate):
    """Models a parameterised Gate with a variable unitary matrix"""

    #params is a dictionary of vars to values
    #entries is a dictionary of coords to entry
    def __init__(self, params, entries, name, qubits, matrix, multi=1,parent=None,image=None):
        super().__init__(name, qubits, matrix, multi,parent,image)
        self.params = params
        self.entries = entries
            
    def get_matr(self):
        """Returns a copy of the unitary matrix which may not contain strings
        returns:
            unit (float[]): unitary matrix in a format without Strings"""
        unit = np.array(copy.deepcopy(self.matrix))
        i = 0
        for row in self.matrix:
            j = 0
            for item in row:
                if(isnan(item)):
                    unit[i,j] = self.param_help(self.entries[(i,j)]) 
                j = j + 1
            i = i + 1
        return unit
    
    def get_matr_formatted(self):
        """Pretty returns the matrix
        returns:
            list (String[]): pretty version of the unitary matrix"""
        list = self.get_unitary().tolist()
        i = 0
        for row in list:
            j = 0
            for item in row:
                try:
                    item = complex(item)
                    list[i][j] = item
                except:
                    list[i][j] = self.entries[(i,j)]
                j = j + 1
            i = i + 1
        return list
    
    def param_help(self,eq):
        """Evaluates a parameter to the unitary matrix
        parameters:
            eq (String): parameter to be evaluated
        returns:
            eq (float): evaluated parameter which should be a number"""
        vars = list(self.params.keys())
        V = len(vars)
        for v in range(V):
            eq = re.sub(vars[v],str(self.params[vars[v]]),eq)
        eq = (eval(eq))
        return eq        

    def get_params(self):
        """Accessor to this Gates parameters
        returns:
            self.params (Dictionary{String:float}): dictionary of parameters"""
        return self.params
    
    def get_entries(self):
        """Accessor to this Gates customisable entries
        returns:
            self.params (Dictionary{(int,int):String): dictionary of entries"""
        return self.entries
    
    def get_unitary(self):
        """Returns unitary matrix in usable format for maths
        returns:
            matr (float[]): fully evaluated matrix"""
        matr = np.array([[None for x in range(len(self.matrix[0]))] for y in range(len(self.matrix))])
        i = 0
        for row in self.matrix:
            j = 0
            for item in row:
                if(isnan(item)):
                    matr[i,j]=self.entries[(i,j)]
                else:
                    matr[i,j]=str(item)
                j = j + 1
            i = i + 1
        return matr

class Accessory():
    """Models an accessory to an accessory"""
    def __init__(self,name,target,dist,mentioned=True,image=None):
        self.name = name
        self.target = target
        self.dist = dist
        self.links = []
        self.mentioned=mentioned
        self.image = image

    def get_name(self):
        """Accessor to this accessory's name
        returns:
            self.name (String): name of this accessory"""
        return self.name
    
    def get_dist(self):
        """Accessor to this accessory's distance from it's target Gate
        returns
            self.dist (int): distance from target"""
        return self.dist
    
    def set_dist(self,d):
        """Mutator to the distance of this gate from it's target
        parameters:
            d (int): new distance from target"""
        self.dist=d
    
    def get_acc(self):
        """Accessor to associated Accessories
        returns:
            accs (Accessory[]): list of associated Accessories"""
        return [self.target]
    
    def is_mentioned(self):
        """Accessor to determine if this accessory is involved in code generation
        returns:
            self.mentioned (Bool): variable which is set at initailisation"""
        return self.mentioned
    
    def get_icon(self):
        """Attemps to return the image associated with this Gate"""
        return self.image
    
