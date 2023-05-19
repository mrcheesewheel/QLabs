import unittest
import model
from math import pi,exp
import numpy as np

class Sprint3Tests(unittest.TestCase):

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.m = model.MainModel()

    def tearDown(self):
        self.m.reset()  

    def test_add_control_2_qub(self):
        self.m.insert_gate(0,0,"Swap")
        self.m.add_control(0,0,self.m.get_entry_at(0,0),self.m.get_entry_at(0,0).getName())
        self.assertEqual(self.m.get_entry_at(0,0).getName(),"Controlled_Swap")
        self.assertEqual(self.m.get_entry_at(0,1).getName(),"Swap input 1")
        self.assertEqual(self.m.get_entry_at(0,2).getName(),"Control")

    def test_create_phase_gate(self):
        res = self.m.create_gate("P",1,[[1,0],[0,"1j * exp(lambda)"]],ps={"lambda":pi},es={(1,1):"exp(1j *lambda)"})
        self.assertIn("P", self.m.operations)

    def test_insert_phase_gate(self):
        res = self.m.create_gate("P",1,[[1,0],[0,"exp(lambda)"]],ps={"lambda":pi},es={(1,1):"exp(lambda)"})
        self.m.insert_gate(3,0,"P",gate_obj=res)
        self.assertEqual(self.m.get_entry_at(0,0),res)
        self.assertDictEqual(self.m.get_entry_at(0,0).getParams(),{"lambda":pi})

    def test_alter_phase_gate_params(self):
        res = self.m.create_gate("P",1,[[1,0],[0,"exp(lambda)"]],ps={"lambda":pi},es={(1,1):"exp(lambda)"})
        self.m.insert_gate(3,0,"P",gate_obj=res)
        self.m.customise_gate(0,0,{"lambda":pi/2})
        self.assertDictEqual(self.m.get_entry_at(0,0).getParams(),{"lambda":pi/2})

    def test_create_toffoli(self):
        res = self.m.create_gate("custX",1,[[0,1],[1,0]])
        self.m.insert_gate(0,0,"custX",res)
        self.m.add_control(0,0,g_n="custX",g_obj=res)
        self.m.add_control(0,0)
        self.assertEqual(self.m.get_entry_at(0,0).getQubits(),3)
        self.assertEqual(len(self.m.get_entry_at(0,0).getMatr()),8)
        self.assertEqual(self.m.get_entry_at(0,0).getMatr()[7][6],1)
        self.assertEqual(self.m.get_entry_at(0,0).getMatr()[6][7],1)
