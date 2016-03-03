import os
from collections import OrderedDict
import re

import Common
import Instructions
import Mif

class Line:

	def __init__(self, fileName, number, string):
		self.FileName = fileName
		self.Number = number
		self.String = string

	def __str__(self):
		return "%s : %s" % (str(self.Number),self.String)

	def __repr__(self):
		return str(self)

class Assembly:

	InterruptVectorTable = {}
	AddressSpaceSize = 65535
	VectorTableStartAddress = 0b1111111111111000

	def __init__(self):
		self.Original = []
		self.WithoutComments = []

		self.Code = []
		self.ConstantsLines = []
		self.DirectivesLines = []

		self.Constants = OrderedDict()
		self.Directives = {}

		self.Instructions = []

	def __str__(self):
		string = ""

		if self.ConstantsLines:
			string += "Constants:"
			for line in self.ConstantsLines:
				string += "\n\t%s" % line
			string += "\n"
		if self.DirectivesLines:
			string += "Directives:"
			for line in self.DirectivesLines:
				string += "\n\t%s" % line
			string += "\n"
		if self.Code:
			string += "Code:"
			for line in self.Code:
				string += "\n\t%s" % line

		return string

	def __repr__(self):
		return str(self)

	def Decode(self):
		self.DecodeConstants()
		self.DecodeDirectives()
		self.DecodeCode()

	def DecodeConstants(self):
		for constant in self.ConstantsLines:
			split = constant.String.split()
			if len(split) != 3:
				Common.Error(constant, "Wrong syntax for constant")
			else:
				self.Constants[Common.NumToHexString(int(split[0],0))] = Common.NumToHexString(int(split[2],0))

	def DecodeDirectives(self):
		for directive in self.DirectivesLines:
			split = directive.String.split()
			if len(split) != 3:
				Common.Error(directive, "Wrong syntax for directive")
			else:
				self.Directives[split[0]] = "0x"+Common.NumToHexString(int(split[2],0))

	def DecodeCode(self):
		newCode = []
		for line in self.Code:
			for directive, value in self.Directives.iteritems():
				extracted = [piece for piece in re.split("\[|\]| |,|\t|\+", line.String)] # Split the instruction by spaces, commas, and brackets
				if directive in extracted:
					line.String = line.String.replace(directive, value)
			if line.String.endswith(':'):
				Common.Error(line, "Label must be on the same line as an instruction")
			self.Instructions.append(Instructions.DecodeLine(line))
			newCode.append(line)
		self.Code = newCode

	@staticmethod
	def ResolveAddresses(instructions, startAddress = 0):
		addressCounter = startAddress
		labelTable = {}
		for instruction in instructions:
			if instruction.Label != None:
				if instruction.Label.startswith("ISR_"):
					num = instruction.Label.replace("ISR_",'')
					if not num.isdigit():
						Common.Error(instruction.Line, "ISR must be followed by a number")
					elif Assembly.VectorTableStartAddress+int(num) > Assembly.AddressSpaceSize:
						Common.Error(instruction.Line, "ISR value is too large. Must not exceed: %s" % str(Assembly.AddressSpaceSize-Assembly.VectorTableStartAddress))
					if int(num) in Assembly.InterruptVectorTable.keys():
						Common.Error(instruction.Line, "Found previous declaration of ISR: %s" % instruction.Label)
					Assembly.InterruptVectorTable[int(num)] = addressCounter
				else:
					if instruction.Label in labelTable.keys():
						Common.Error(instruction.Line, "Found previous declaration of label: %s" % instruction.Label)
					labelTable[instruction.Label] = addressCounter
			addressCounter += 1
		for instruction in instructions:
			if instruction.NeedsLabelAddress:
				if instruction.LabelOperand in labelTable.keys():
					instruction.Address = labelTable[instruction.LabelOperand]
					instruction.Assemble()
				else:
					Common.Error(instruction.Line, "Could not find destination label for: %s" % instruction.LabelOperand)

class Parser:

	def __init__(self, assemblyFilePath):
		self.AssemblyFilePath = assemblyFilePath
		self.Assembly = Assembly()

	def FileToLines(self, assemblyFilePath):
		if os.path.isfile(assemblyFilePath):
			with open(assemblyFilePath) as _file:
				lineCount = 1
				for line in _file:
					self.Assembly.Original.append(Line(os.path.basename(assemblyFilePath), lineCount, line.strip()))
					lineCount+=1
		else: 
			return []

	def GetAssemblyData(self):
		lines = []
		for instruction in self.Assembly.Instructions:
			data = Common.NumToHexString(int(instruction.MachineCode, 2), 8)
			comment = instruction.Line.String.replace('\t','')
			lines.append(Mif.MifLine(data=data, comment=comment, instruction=instruction))
		return lines

	def GetConstantsData(self):
		lines = []
		for address, data in self.Assembly.Constants.iteritems():
			lines.append(Mif.MifLine(data=data, address=address))
		return lines

	@staticmethod
	def GetInterruptVectorTable():
		lines = []
		for num, dest in Assembly.InterruptVectorTable.iteritems():
			dest = Common.NumToHexString(dest, 8)
			lines.append(Mif.MifLine(address=Assembly.VectorTableStartAddress+num, data=dest, comment="ISR_%i" % num))
		return lines

	def RemoveComments(self):
		pass1 =  [line for line in self.Assembly.Original if not line.String.startswith(";") and not line.String.startswith("//")] # Removes all lines starting with semicolons
		pass2 = []
		for line in pass1:
			if ';' in line.String:
				line.String = line.String[:line.String.index(';')] # Removes semicolon comments
			if "//" in line.String:
				line.String = line.String[:line.String.index("//")] # Removes // comments
			pass2.append(line)

		return [line for line in pass2 if line.String != ""] # Remove empty lines

	def Separate(self):
		category = Common.Enum("Directives", "Constants", "Code")
		myCategory = None

		for line in self.Assembly.WithoutComments:
			if line.String.startswith('.directives'):
				myCategory = category.Directives
			elif line.String.startswith('.constants'):
				myCategory = category.Constants
			elif line.String.startswith('.code'):
				myCategory = category.Code
			elif line.String.startswith('.enddirectives') or line.String.startswith('.endconstants') or line.String.startswith('.endcode'):
				myCategory = None
			else:
				if myCategory == category.Directives:
					self.Assembly.DirectivesLines.append(line)
				elif myCategory == category.Constants:
					self.Assembly.ConstantsLines.append(line)
				elif myCategory == category.Code:
					if "=" in line.String:
						self.Assembly.DirectivesLines.append(line)
					else:
						self.Assembly.Code.append(line)
				else:
					Common.Error(line, "Line \"%s\" belongs to unknown section" % line.String)

	def Parse(self):
		self.FileToLines(self.AssemblyFilePath)
		self.Assembly.WithoutComments = self.RemoveComments()
		self.Separate()
		self.Assembly.Decode()
