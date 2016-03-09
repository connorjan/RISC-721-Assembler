import Common
import InstructionBase

def DecodeLine(line):
	instruction = None
	label = None
	if line.String.split()[0].endswith(':'):
		mnemonic = line.String.split()[1].upper()
	else:
		mnemonic = line.String.split()[0].upper()

	if mnemonic not in InstructionBase.InstructionList.keys():
		Common.Error(line, "Unknown instruction: %s" % mnemonic)

	opCode = InstructionBase.InstructionList[mnemonic]
	if (opCode == 0x0 or opCode == 0x1):
		instruction = LoadStore(line, mnemonic, opCode)
	elif (opCode == 0x2 or opCode == 0x3 or opCode == 0x4):
		instruction = DataTransfer(line, mnemonic, opCode)
	elif (opCode == 0x5 or opCode == 0x6 or opCode == 0x7):
		instruction = FlowControl(line, mnemonic, opCode)
	elif (0x8 <= opCode and opCode <= 0xF) or (0x11 <= opCode and opCode <= 0x14):
		instruction = LogicUnit(line, mnemonic, opCode)
	elif (opCode == 0x10):
		instruction = RotateShift(line, mnemonic, opCode)
	elif (opCode == 0xFF):
		instruction = Emulated(line, mnemonic, opCode)
	else:
		Common.Error(line, "Unknown opCode %i for instruction: %s" % (opCode, mnemonic))

	instruction.Decode()
	return instruction

class LoadStore(InstructionBase.InstructionBase_):

	def __init__(self, line, mnemonic, opCode):
		super(LoadStore, self).__init__(line, mnemonic, opCode)
		self.Ri = None
		self.Rj = None
		self.Control = None
		self.Address = 0

	def Decode(self):
		if len(self.SplitLine) != 3 and len(self.SplitLine) != 4:
				Common.Error(self.Line, "Wrong number of operands")
		elif self.Mnemonic == "LD":
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetAddressOperand(self.SplitLine[2])
		elif self.Mnemonic == "ST":
			self.GetAddressOperand(self.SplitLine[1])
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Ri)
		else:
			Common.Error(self.Line, "Error in Decode")
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		self.MachineCode += Common.NumToBinaryString(self.Address, 16)
		return self

class DataTransfer(InstructionBase.InstructionBase_):

	def __init__(self, line, mnemonic, opCode):
		super(DataTransfer, self).__init__(line, mnemonic, opCode)
		self.Ri = 0
		self.Rj = 0
		self.Control = 0
		self.Constant = 0

	def Decode(self):
		if self.Mnemonic == "CPY":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1],self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2],self.RegisterField.Rj)
		elif self.Mnemonic == "CPYC":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1],self.RegisterField.Ri)
			self.GetConstantOperand(self.SplitLine[2])
			self.Control = 1
		elif self.Mnemonic == "PUSH":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1],self.RegisterField.Rj)
		elif self.Mnemonic == "PUSHC":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetConstantOperand(self.SplitLine[1])
			self.Control = 1
		elif self.Mnemonic == "POP":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1],self.RegisterField.Ri)
		else:
			Common.Error(self.Line, "Error in Decode")
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		self.MachineCode += Common.NumToBinaryString(self.Constant, 16)
		return self

class FlowControl(InstructionBase.InstructionBase_):

	JumpConditions = { 	"JU"	: 0x0,
						"JMP"	: 0x0,
						"JC"	: 0x8,
						"JN"	: 0x4,
						"JV"	: 0x2,
						"JZ"	: 0x1,
						"JEQ"	: 0x1,
						"JNC"	: 0x7,
						"JNN"	: 0xB,
						"JNV"	: 0xD,
						"JNZ"	: 0xE,
						"JNE"	: 0xE,
						"JGE"	: 0x6,
						"JL"	: 0x9 }

	def __init__(self, line, mnemonic, opCode):
		super(FlowControl, self).__init__(line, mnemonic, opCode)
		self.Ri = 0
		self.CNVZ = 0
		self.Control = 0
		self.Address = None

		self.LabelOperand = None
		
	def Decode(self):
		if self.Mnemonic == "RET" or self.Mnemonic == "RETI" :
			if len(self.SplitLine) != 1:
				Common.Error(self.Line, "Wrong number of operands")
			self.Address = 0
			if self.Mnemonic == "RETI":
				self.Control = 1
		else:
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.NeedsLabelAddress = True
			self.Control = 1
			self.LabelOperand = self.SplitLine[1]
			if self.Mnemonic in self.JumpConditions.keys():
				self.CNVZ = self.JumpConditions[self.Mnemonic]
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.CNVZ, 4)
		self.MachineCode += Common.NumToBinaryString(0, 1)
		self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		self.MachineCode += Common.NumToBinaryString(self.Address, 16)
		return self

class LogicUnit(InstructionBase.InstructionBase_):

	def __init__(self, line, mnemonic, opCode):
		super(LogicUnit, self).__init__(line, mnemonic, opCode)
		self.Ri = None
		self.Rj = 0
		self.Rk = None
		self.Control = None
		self.Constant = None

	def Decode(self):
		if self.Mnemonic == "CMP":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Rj)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rk)
		elif self.Mnemonic == "CMPC":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Rj)
			self.GetConstantOperand(self.SplitLine[2])
			self.Control = 1
		elif self.Mnemonic == "NOT":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rj)
		elif self.Mnemonic == "NOTC":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetConstantOperand(self.SplitLine[2])
			self.Control = 1
		elif self.Mnemonic == "ADDC" or self.Mnemonic == "SUBC" or self.Mnemonic == "ANDC" or self.Mnemonic == "BICC" or self.Mnemonic == "ORC" or self.Mnemonic == "XORC":
			if len(self.SplitLine) != 4:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rj)
			self.GetConstantOperand(self.SplitLine[3])
			self.Control = 1
		else:
			if len(self.SplitLine) != 4:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rj)
			self.GetRegisterOperand(self.SplitLine[3], self.RegisterField.Rk)
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		if (self.Ri != None):
			self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		else:
			self.MachineCode += Common.NumToBinaryString(0, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		if (self.Rk != None):
			self.MachineCode += Common.NumToBinaryString(self.Rk, 5)
			self.MachineCode += Common.NumToBinaryString(0, 12)
		elif (self.Constant != None and self.Control != None):
			self.MachineCode += Common.NumToBinaryString(self.Constant, 16)
			self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		else:
			self.MachineCode += Common.NumToBinaryString(0, 17)
		return self

class RotateShift(InstructionBase.InstructionBase_):

	Conditions = { 	"SRL"	: 0x0,
					"SLL"	: 0x1,
					"SRA"	: 0x2,
					"RTR"	: 0x4,
					"RTL"	: 0x5,
					"RRC"	: 0x6,
					"RLC"	: 0x7 }

	def __init__(self, line, mnemonic, opCode):
		super(RotateShift, self).__init__(line, mnemonic, opCode)
		self.Ri = 0
		self.Rj = 0
		self.Control = 0
		self.Constant = 0

	def Decode(self):
		if len(self.SplitLine) != 4:
				Common.Error(self.Line, "Wrong number of operands")
		elif self.Mnemonic in self.Conditions:
			self.Control = self.Conditions[self.Mnemonic]
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rj)
			self.GetConstantOperand(self.SplitLine[3])
		else:
			Common.Error(self.Line, "Error in Decode")
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		self.MachineCode += Common.NumToBinaryString(self.Control, 3)
		self.MachineCode += Common.NumToBinaryString(self.Constant, 6)
		self.MachineCode += Common.NumToBinaryString(0, 8)
		return self

class Emulated(InstructionBase.InstructionBase_):

	def __init__(self, line, mnemonic, opCode):
		super(Emulated, self).__init__(line, mnemonic, opCode)
		self.Ri = 0
		self.Rj = 0
		self.Rk = None
		self.Control = 0
		self.Constant = None

	def Decode(self):
		if self.Mnemonic == "INC":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.OpCode = InstructionBase.InstructionList["ADD"]
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.Rj = self.Ri
			self.Control = 1
			self.Constant = 1
		elif self.Mnemonic == "DEC":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.OpCode = InstructionBase.InstructionList["SUB"]
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.Rj = self.Ri
			self.Control = 1
			self.Constant = 1
		elif self.Mnemonic == "CLR":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.OpCode = InstructionBase.InstructionList["SUB"]
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.Rj = self.Ri
			self.Rk = self.Rj
		elif self.Mnemonic == "CLRC":
			self.OpCode = InstructionBase.InstructionList["BICC"]
			# Ri and Rj are 0, the status register
			self.Common.Error(self.Line, "CLRC not possible right now.")
		elif self.Mnemonic == "NOP":
			self.OpCode = InstructionBase.InstructionList["CPY"]
			self.Ri = 1
			self.Rj = 1
		else:
			Common.Error(self.Line, "Error in Decode")
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		if (self.Rk != None):
			self.MachineCode += Common.NumToBinaryString(self.Rk, 5)
			self.MachineCode += Common.NumToBinaryString(0, 12)
		elif (self.Constant != None):
			self.MachineCode += Common.NumToBinaryString(self.Constant, 16)
			self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		else:
			self.MachineCode += Common.NumToBinaryString(0, 17)
		return self
