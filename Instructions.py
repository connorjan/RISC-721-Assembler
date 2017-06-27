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
	instruction = GetInstructionClass(line, mnemonic, opCode)

	instruction.Decode()
	return instruction

def Encode(word):
	instruction = None
	opCode = Common.SliceBits(word.Data, 31, 27)

	if opCode not in InstructionBase.MnemonicList.keys():
		Common.Error(word.Line, "Unknown opcode: %s" % opCode)

	mnemonic = InstructionBase.MnemonicList[opCode]
	
	instruction = GetInstructionClass(word.Line, mnemonic, opCode)
	instruction.MachineCodeAddress = word.Address
	instruction.MachineCodeValue = word.Data
	instruction.Encode()

	return instruction

def GetInstructionClass(line, mnemonic, opCode):
	if (opCode == 0x0 or opCode == 0x1):
		return LoadStore(line, mnemonic, opCode)
	elif (opCode == 0x2 or opCode == 0x3 or opCode == 0x4):
		return DataTransfer(line, mnemonic, opCode)
	elif (opCode == 0x5 or opCode == 0x6 or opCode == 0x7):
		return FlowControl(line, mnemonic, opCode)
	elif (0x8 <= opCode and opCode <= 0xF) or (0x11 <= opCode and opCode <= 0x16):
		return LogicUnit(line, mnemonic, opCode)
	elif (opCode == 0x10):
		return RotateShift(line, mnemonic, opCode)
	elif (opCode == 0xFF):
		return Emulated(line, mnemonic, opCode)
	else:
		Common.Error(line, "Unknown opCode %i for instruction: %s" % (opCode, mnemonic))

class LoadStore(InstructionBase.InstructionBase_):

	def __init__(self, line, mnemonic, opCode):
		super(LoadStore, self).__init__(line, mnemonic, opCode)
		self.Ri = None
		self.Rj = None
		self.Control = None
		self.Address = 0

	def __str__(self):
		s = "Instruction = {}\n".format(self.Mnemonic)
		s += "\tRi = {}\n".format(self.Ri)
		s += "\tRj = {}\n".format(self.Rj)
		s += "\tControl = {}\n".format(self.Control)
		s += "\tAddress = 0x{:04X}".format(self.Address)
		return s

	def Decode(self):
		if len(self.SplitLine) == 4 or len(self.SplitLine) == 5:
			if self.Mnemonic == "LD":
				newSplitLine = self.SplitLine[0:2]
				newSplitLine.append(self.SplitLine[2] + '+' + self.SplitLine[len(self.SplitLine)-1])
				self.SplitLine = newSplitLine
			elif self.Mnemonic == "ST":
				newSplitLine = self.SplitLine[0:1]
				newSplitLine.append(self.SplitLine[1] + '+' + self.SplitLine[len(self.SplitLine)-2])
				newSplitLine.append(self.SplitLine[len(self.SplitLine)-1])
				self.SplitLine = newSplitLine

		try:
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			elif self.Mnemonic == "LD":
				self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
				self.GetAddressOperand(self.SplitLine[2])
			elif self.Mnemonic == "ST":
				self.GetAddressOperand(self.SplitLine[1])
				self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Ri)
			else:
				Common.Error(self.Line, "Error in Decode")

		except Exception:
			Common.Error(self.Line, "Could not decode addressing mode")

		return self

	def Encode(self):
		self.Ri = Common.SliceBits(self.MachineCodeValue, 26, 22)
		self.Rj = Common.SliceBits(self.MachineCodeValue, 21, 17)
		self.Control = Common.SliceBits(self.MachineCodeValue, 16)
		self.Address = Common.SliceBits(self.MachineCodeValue, 15, 0)
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		self.MachineCode += Common.NumToBinaryString(self.Address, 16)
		return self

	def Disassemble(self):
		operands = []
		if InstructionBase.MnemonicList[self.OpCode] == "LD":
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Ri))
			operands.append(self.DecodeAddressOperand())
		else: # if ST
			operands.append(self.DecodeAddressOperand())
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Ri))
		self.DisassembledString = self.BuildDisassembledString(self.Mnemonic, operands)
		return self


class DataTransfer(InstructionBase.InstructionBase_):

	def __init__(self, line, mnemonic, opCode):
		super(DataTransfer, self).__init__(line, mnemonic, opCode)
		self.Ri = 0
		self.Rj = 0
		self.Control = 0
		self.Constant = 0

	def __str__(self):
		s = "Instruction = {}\n".format(self.Mnemonic)
		s += "\tRi = {}\n".format(self.Ri)
		s += "\tRj = {}\n".format(self.Rj)
		s += "\tControl = {}\n".format(self.Control)
		s += "\tConstant = 0x{:04X}".format(self.Constant)
		return s

	def Decode(self):
		if self.Mnemonic == "CPY":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1],self.RegisterField.Ri)
			self.GetEitherOperand(self.SplitLine[2],self.RegisterField.Rj)
		elif self.Mnemonic == "CPYC":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1],self.RegisterField.Ri)
			self.GetConstantOperand(self.SplitLine[2])
		elif self.Mnemonic == "PUSH":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetEitherOperand(self.SplitLine[1],self.RegisterField.Rj)
		elif self.Mnemonic == "PUSHC":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetConstantOperand(self.SplitLine[1])
		elif self.Mnemonic == "POP":
			if len(self.SplitLine) != 2:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1],self.RegisterField.Ri)
		else:
			Common.Error(self.Line, "Error in Decode")
		return self

	def Encode(self):
		self.Ri = Common.SliceBits(self.MachineCodeValue, 26, 22)
		self.Rj = Common.SliceBits(self.MachineCodeValue, 21, 17)
		self.Control = Common.SliceBits(self.MachineCodeValue, 16)
		self.Constant = Common.SliceBits(self.MachineCodeValue, 15, 0)
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		self.MachineCode += Common.NumToBinaryString(self.Constant, 16)
		return self

	def Disassemble(self):
		operands = []
		if InstructionBase.MnemonicList[self.OpCode] == "CPY":
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Ri))
			operands.append(self.DecodeEitherOperand(self.RegisterField.Rj))
		elif InstructionBase.MnemonicList[self.OpCode] == "PUSH":
			operands.append(self.DecodeEitherOperand(self.RegisterField.Rj))
		elif InstructionBase.MnemonicList[self.OpCode] == "POP":
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Ri))
		self.DisassembledString = self.BuildDisassembledString(self.Mnemonic, operands)
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

	JumpConditionsMnemonic = {
						0x0	:	"JMP",
						0x8	:	"JC",
						0x4	:	"JN",
						0x2	:	"JV",
						0x1	:	"JEQ",
						0x7	:	"JNC",
						0xB	:	"JNN",
						0xD	:	"JNV",
						0xE	:	"JNE",
						0x6	:	"JGE",
						0x9	:	"JL" }

	def __init__(self, line, mnemonic, opCode):
		super(FlowControl, self).__init__(line, mnemonic, opCode)
		self.Ri = 0
		self.CNVZ = 0
		self.Control = 0
		self.Address = None

		self.LabelOperand = None

	def __str__(self):
		s = "Instruction = {}\n".format(self.JumpConditionsMnemonic[self.CNVZ])
		s += "\tRi = {}\n".format(self.Ri)
		s += "\tCNVZ = 0b{:04b}\n".format(self.CNVZ)
		s += "\tControl = {}\n".format(self.Control)
		s += "\tAddress = 0x{:04X}".format(self.Address)
		return s
		
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
			# else: it is a CALL instruction
		return self

	def Encode(self):
		self.Ri = Common.SliceBits(self.MachineCodeValue, 26, 22)
		self.CNVZ = Common.SliceBits(self.MachineCodeValue, 21, 18)
		self.Control = Common.SliceBits(self.MachineCodeValue, 16)
		self.Address = Common.SliceBits(self.MachineCodeValue, 15, 0)
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.CNVZ, 4)
		self.MachineCode += Common.NumToBinaryString(0, 1)
		self.MachineCode += Common.NumToBinaryString(self.Control, 1)
		self.MachineCode += Common.NumToBinaryString(self.Address, 16)
		return self

	def Disassemble(self):
		operands = []
		if InstructionBase.MnemonicList[self.OpCode] == "CALL":
			self.NeedsLabelOperand = True
		elif InstructionBase.MnemonicList[self.OpCode] != "RET":
			self.Mnemonic = self.JumpConditionsMnemonic[self.CNVZ]
			self.NeedsLabelOperand = True

		if not self.NeedsLabelOperand:
			self.DisassembledString = self.BuildDisassembledString(self.Mnemonic, operands)
		return self


class LogicUnit(InstructionBase.InstructionBase_):

	def __init__(self, line, mnemonic, opCode):
		super(LogicUnit, self).__init__(line, mnemonic, opCode)
		self.Ri = None
		self.Rj = 0
		self.Rk = None
		self.Control = None
		self.Constant = None

	def __str__(self):
		s = "Instruction = {}\n".format(self.Mnemonic)
		s += "\tRi = {}\n".format(self.Ri)
		s += "\tRj = {}\n".format(self.Rj)
		s += "\tRk = {}\n".format(self.Rk)
		s += "\tControl = {}".format(1 if self.Control else 0)
		if self.Constant is not None:
			s += "\n\tConstant = 0x{:04X}".format(self.Constant)
		return s

	def Decode(self):
		if self.Mnemonic == "CMP":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Rj)
			self.GetEitherOperand(self.SplitLine[2], self.RegisterField.Rk)
		elif self.Mnemonic == "CMPC":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Rj)
			self.GetConstantOperand(self.SplitLine[2])
		elif self.Mnemonic == "NOT" or self.Mnemonic == "FTI" or self.Mnemonic == "ITF":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetEitherOperand(self.SplitLine[2], self.RegisterField.Rj)
		elif self.Mnemonic == "NOTC":
			if len(self.SplitLine) != 3:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetConstantOperand(self.SplitLine[2])
		elif self.Mnemonic == "ADDC" or self.Mnemonic == "SUBC" or self.Mnemonic == "ANDC" or self.Mnemonic == "BICC" or self.Mnemonic == "ORC" or self.Mnemonic == "BISC" or self.Mnemonic == "XORC":
			if len(self.SplitLine) != 4:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rj)
			self.GetConstantOperand(self.SplitLine[3])
		else:
			if len(self.SplitLine) != 4:
				Common.Error(self.Line, "Wrong number of operands")
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rj)
			self.GetEitherOperand(self.SplitLine[3], self.RegisterField.Rk)
		return self

	def Encode(self):
		self.Ri = Common.SliceBits(self.MachineCodeValue, 26, 22)
		self.Rj = Common.SliceBits(self.MachineCodeValue, 21, 17)
		self.Control = Common.SliceBits(self.MachineCodeValue, 0)
		if self.Control:
			self.Constant = Common.SliceBits(self.MachineCodeValue, 16, 1)
		else:
			self.Rk = Common.SliceBits(self.MachineCodeValue, 16, 12)
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

	def Disassemble(self):
		operands = []
		if InstructionBase.MnemonicList[self.OpCode] == "CMP":
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Rj))
			operands.append(self.DecodeEitherOperand(self.RegisterField.Rk))
		elif InstructionBase.MnemonicList[self.OpCode] == "NOT":
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Ri))
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Rj))
		else:
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Ri))
			operands.append(self.DecodeRegisterOperand(self.RegisterField.Rj))
			operands.append(self.DecodeEitherOperand(self.RegisterField.Rk))
		self.DisassembledString = self.BuildDisassembledString(self.Mnemonic, operands)
		return self

class RotateShift(InstructionBase.InstructionBase_):

	Conditions = {  "SRL"	: 0x0,
					"SRLC"	: 0x0,
					"SLL"	: 0x1,
					"SLLC"	: 0x1,
					"SRA"	: 0x2,
					"SRAC"	: 0x2,
					"RTR"	: 0x4,
					"RTRC"	: 0x4,
					"RTL"	: 0x5,
					"RTLC"	: 0x5,
					"RRC"	: 0x6,
					"RRCC"	: 0x6,
					"RLC"	: 0x7,
					"RLCC"	: 0x7
				}

	ConditionsMnemonic = {
					0x0	:	"SRL",
					0x1	:	"SLL",
					0x2	:	"SRA",
					0x4	:	"RTR",
					0x5	:	"RTL",
					0x6	:	"RRC",
					0x7	:	"RLC",
	}

	def __init__(self, line, mnemonic, opCode):
		super(RotateShift, self).__init__(line, mnemonic, opCode)
		self.Ri = 0
		self.Rj = 0
		self.Rk = None
		self.Constant = None
		self.Condition = 0	

	def __str__(self):
		s = "Instruction = {}\n".format(self.ConditionsMnemonic[self.Condition])
		s += "\tRi = {}\n".format(self.Ri)
		s += "\tRj = {}\n".format(self.Rj)
		s += "\tRk = {}\n".format(self.Rk)
		s += "\tConstant = 0x{:04X}\n".format(self.Constant)
		s += "\tCondition = {}".format(self.Condition)
		return s

	def Decode(self):
		if len(self.SplitLine) != 4:
				Common.Error(self.Line, "Wrong number of operands")
		elif self.Mnemonic in self.Conditions:
			self.Condition = self.Conditions[self.Mnemonic]
			self.GetRegisterOperand(self.SplitLine[1], self.RegisterField.Ri)
			self.GetRegisterOperand(self.SplitLine[2], self.RegisterField.Rj)
			self.GetEitherOperand(self.SplitLine[3], self.RegisterField.Rk)
		else:
			Common.Error(self.Line, "Error in Decode")
		return self

	def Encode(self):
		self.Ri = Common.SliceBits(self.MachineCodeValue, 26, 22)
		self.Rj = Common.SliceBits(self.MachineCodeValue, 21, 17)
		self.Control = Common.SliceBits(self.MachineCodeValue, 0)
		if self.Control:
			self.Constant = Common.SliceBits(self.MachineCodeValue, 16, 11)
		else:
			self.Rk = Common.SliceBits(self.MachineCodeValue, 16, 12)
		self.Condition = Common.SliceBits(self.MachineCodeValue, 3, 1)
		return self

	def Assemble(self):
		self.MachineCode += Common.NumToBinaryString(self.OpCode, 5)
		self.MachineCode += Common.NumToBinaryString(self.Ri, 5)
		self.MachineCode += Common.NumToBinaryString(self.Rj, 5)
		if self.Rk != None:
			self.MachineCode += Common.NumToBinaryString(self.Rk, 5)
			self.MachineCode += Common.NumToBinaryString(0, 8)
		else:
			self.MachineCode += Common.NumToBinaryString(self.Constant, 6)
			self.MachineCode += Common.NumToBinaryString(0, 7)
		self.MachineCode += Common.NumToBinaryString(self.Condition, 3)
		if self.Rk != None:
			self.MachineCode += Common.NumToBinaryString(0, 1)
		else:
			self.MachineCode += Common.NumToBinaryString(1, 1)
		return self

	def Disassemble(self):
		operands = []
		self.Mnemonic = self.ConditionsMnemonic[self.Condition]
		operands.append(self.DecodeRegisterOperand(self.RegisterField.Ri))
		operands.append(self.DecodeRegisterOperand(self.RegisterField.Rj))
		operands.append(self.DecodeEitherOperand(self.RegisterField.Rk))
		self.DisassembledString = self.BuildDisassembledString(self.Mnemonic, operands)
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
			self.OpCode = InstructionBase.InstructionList["BIC"]
			# Ri and Rj are 0, the status register
			self.Ri = 0
			self.Rj = 0
			self.Control = 1
			self.Constant = 1
		elif self.Mnemonic == "SETC":
			self.OpCode = InstructionBase.InstructionList["OR"]
			# Ri and Rj are 0, the status register
			self.Ri = 0
			self.Rj = 0
			self.Control = 1
			self.Constant = 1
		elif self.Mnemonic == "NOP":
			self.OpCode = InstructionBase.InstructionList["CPY"]
			self.Ri = 0
			self.Rj = 0
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
