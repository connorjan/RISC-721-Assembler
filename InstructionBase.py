import re
import Common

class InstructionBase_(object):

	RegisterWidth = 32
	RegisterField = Common.Enum("Ri", "Rj", "Rk")

	def __init__(self, line, mnemonic, opCode):
		self.Line = line
		self.Label = None
		self.Mnemonic = mnemonic
		self.MachineCode = ""
		self.NeedsLabelAddress = False
		self.OpCode = opCode
		self.SplitLine = [piece for piece in re.split(" |,|\t", self.Line.String) if piece != '']
		if self.SplitLine[0].endswith(':'):
			self.Label = self.SplitLine[0][0:len(self.SplitLine[0])-1]
			self.SplitLine = self.SplitLine[1:]

	def Assemble(self):
		Common.Error(self.Line, "This instruction did not implement the method: Assemble")

	def Decode(self):
		Common.Error(self.Line, "This instruction did not implement the method: Decode")

	def GetAddressOperand(self, arg):
		# strip M[], figure out what the control is, do stuff based off of the control.
		operand = arg.replace("M[",'').replace(']','')
		if '+' in operand:
			self.Control = 0
			operand = operand.split('+')
			if operand[0] == "PC":
				# PC Relative
				self.Rj = 0
				self.Address = int(operand[1],0)
			elif operand[1] == "PC":
				# PC Relative
				self.Rj = 0
				self.Address = int(operand[0],0)
			elif operand[0].startswith("0x"):
				# Indexed
				self.Address = int(operand[0],0)
				self.GetRegisterOperand(operand[1],self.RegisterField.Rj)
			elif operand[1].startswith("0x"):
				# Indexed
				self.Address = int(operand[1],0)
				self.GetRegisterOperand(operand[0],self.RegisterField.Rj)
			else:
				Common.Error(self.Line, "Invalid operand for address: %s" % arg)
		else:
			if operand.startswith("R"):
				# Register direct
				self.Control = 1
				self.GetRegisterOperand(operand, self.RegisterField.Rj)
			elif operand == "PC":
				# PC Relative with no offset
				self.Control = 0
				self.Rj = 0
				self.Address = 0
			else:
				# Absolute addressing mode
				self.Control = 1
				self.Rj = 0
				try:
					self.Address = int(operand,0)
				except Exception:
					Common.Error(self.Line, "Invalid address operand: %s" % operand)

	def GetConstantOperand(self, operand):
		try:
			self.Constant = int(operand,0)
		except ValueError:
			Common.Error(self.Line, "Constant must be a number: %s" % operand)
		
		self.Control = 1

	def GetEitherOperand(self, operand, registerField):
		if operand[0] == 'R':
			self.GetRegisterOperand(operand, registerField)
		else:
			self.GetConstantOperand(operand)

	def GetRegisterOperand(self, operand, registerField):
		if operand[0] != 'R' or not operand[1:].isdigit():
			Common.Error(self.Line, "Invalid operand for register: %s" % operand)
		elif registerField == self.RegisterField.Ri:
			self.Ri = int(operand[1:])
		elif registerField == self.RegisterField.Rj:
			self.Rj = int(operand[1:])
		elif registerField == self.RegisterField.Rk:
			self.Rk = int(operand[1:])
		else:
			Common.Error(self.Line, "We should never get here")

# This encodes the instruction mnemonic to the opcode
InstructionList = {	"LD" 	: 0x00, 
					"ST" 	: 0x01,
					"CPY" 	: 0x02,
					"CPYC" 	: 0x02,
					"PUSH"	: 0x03,
					"PUSHC"	: 0x03,
					"POP"	: 0x04,
					"JU"	: 0x05,
					"JMP"	: 0x05,
					"JC"	: 0x05,
					"JNC"	: 0x05,
					"JN"	: 0x05,
					"JNN"	: 0x05,
					"JV"	: 0x05,
					"JNV"	: 0x05,
					"JZ"	: 0x05,
					"JEQ"	: 0x05,
					"JNZ"	: 0x05,
					"JNE"	: 0x05,
					"JGE"	: 0x05,
					"JL"	: 0x05,
					"CALL"	: 0x06, 
					"RET"	: 0x07,
					"RETI"	: 0x07,
					"ADD"	: 0x08,
					"ADDC"	: 0x08,
					"SUB"	: 0x09,
					"SUBC"	: 0x09,
					"CMP"	: 0x0A,
					"CMPC"	: 0x0A,
					"NOT" 	: 0x0B,
					"NOTC" 	: 0x0B,
					"AND"	: 0x0C,
					"ANDC"	: 0x0C,
					"BIC"	: 0x0D,
					"BICC"	: 0x0D,
					"OR"	: 0x0E,
					"ORC"	: 0x0E,
					"BIS"	: 0x0E,
					"BISC"	: 0x0E,
					"XOR"	: 0x0F,
					"XORC"	: 0x0F,
					"SRL"	: 0x10,
					"SRLC"	: 0x10,
					"SLL"	: 0x10,
					"SLLC"	: 0x10,
					"SRA"	: 0x10,
					"SRAC"	: 0x10,
					"RTR"	: 0x10,
					"RTRC"	: 0x10,
					"RTL"	: 0x10,
					"RTLC"	: 0x10,
					"RRC"	: 0x10,
					"RRCC"	: 0x10,
					"RLC"	: 0x10,
					"RLCC"	: 0x10,
					"FA"	: 0x11,
					"FS"	: 0x12,
					"FM"	: 0x13,
					"FD"	: 0x14,
					"FTI"	: 0x15,
					"ITF"	: 0x16,

					# Emulated instructions
					"INC" 	: 0xFF,
					"DEC" 	: 0xFF,
					"CLR" 	: 0xFF,
					"CLRC" 	: 0xFF,
					"SETC" 	: 0xFF,
					"NOP" 	: 0xFF
					}
