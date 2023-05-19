import unittest
import model
from math import *

class Sprint1Tests(unittest.TestCase):

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.m = model.MainModel()

    def tearDown(self):
        self.m.reset()        

    def test_insert_1_qub_gate(self):
        self.m.insert_gate(3,0,"Hadamard")
        self.assertEqual(self.m.get_entry_at(0,0).getName(),"Hadamard")

    def test_insert_2_qub_gate(self):
        self.m.insert_gate(0,0,"Controlled_X")
        self.assertEqual(self.m.get_entry_at(0,0).getName(),"Controlled_X")
        self.assertEqual(self.m.get_entry_at(0,1).getName(),"Control")

    def test_displace_inserts(self):
        self.m.insert_gate(0,0,"Controlled_X")
        self.m.insert_gate(0,1,"Hadamard")
        self.assertEqual(self.m.get_entry_at(0,1).getName(),"Hadamard")
        self.assertEqual(self.m.get_entry_at(1,0).getName(),"Controlled_X")
        self.assertEqual(self.m.get_entry_at(1,1).getName(),"Control")
    
    