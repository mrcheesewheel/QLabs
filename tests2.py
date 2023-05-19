import unittest
import model

class Sprint2Tests(unittest.TestCase):

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.m = model.MainModel()

    def setUp(self):
        self.m.insert_gate(0,0,"Controlled_X")
        self.m.insert_gate(0,1,"Hadamard")

    def tearDown(self) -> None:
        self.m.reset()

    def test_remove_on_target(self):
        self.m.insert_gate(0,0,"Controlled_X")
        self.m.insert_gate(0,1,"Hadamard")
        self.m.remove_gate(0,1)
        self.assertEqual(self.m.get_entry_at(0,0).getName(),"Controlled_X")
        self.assertEqual(self.m.get_entry_at(0,1).getName(),"Control")
    
    def test_remove_on_accessory(self):
        self.m.insert_gate(0,0,"Controlled_X")
        self.m.insert_gate(0,1,"Hadamard")
        self.m.move_acc(1,1,1,2)
        self.m.remove_gate(1,1)
        self.assertEqual(self.m.get_entry_at(0,1).getName(),"Hadamard")
        self.assertEqual(self.m.get_entry_at(1,0),None)
        self.assertEqual(self.m.get_entry_at(1,1),None)
        self.assertEqual(self.m.get_entry_at(1,2),None)

    def test_move_accessory(self):
        self.m.move_acc(1,1,1,2)
        self.assertEqual(self.m.get_entry_at(0,1).getName(),"Hadamard")
        self.assertEqual(self.m.get_entry_at(1,0).getName(),"Controlled_X")
        self.assertEqual(self.m.get_entry_at(1,1).getName(),"Link")
        self.assertEqual(self.m.get_entry_at(1,2).getName(),"Control")

    def test_move_1_qubit_gate(self):
        self.m.move_gate(0,1,0,0)
        self.assertEqual(self.m.get_entry_at(0,0).getName(),"Hadamard")
        self.assertEqual(self.m.get_entry_at(1,0).getName(),"Controlled_X")
        self.assertEqual(self.m.get_entry_at(1,1).getName(),"Control")

    def test_move_2_qubit_gate(self):
        self.m.move_gate(0,1,0,0)
        self.m.move_gate(1,0,0,1)
        self.assertEqual(self.m.get_entry_at(0,0).getName(),"Hadamard")
        self.assertEqual(self.m.get_entry_at(0,1).getName(),"Controlled_X")
        self.assertEqual(self.m.get_entry_at(0,2).getName(),"Control")