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
	AddressSpaceSize = None
	VectorTableStartAddress = None

	def __init__(self, addressWidth):
		self.Original = []
		self.WithoutComments = []

		self.Code = []
		self.ConstantsLines = []
		self.DirectivesLines = []

		self.Constants = OrderedDict()
		self.Directives = {}

		self.Instructions = []

		Assembly.AddressSpaceSize = (2**addressWidth) - 1
		Assembly.VectorTableStartAddress = Assembly.AddressSpaceSize - (2**3 - 1)

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
			split = constant.String.split("=")
			split = [piece.strip() for piece in split]
			if len(split) != 2:
				Common.Error(constant, "Wrong syntax for constant")
			else:
				self.Constants[Common.ExprToHexString(split[0],constant)] = (Common.ExprToHexString(split[1],constant), constant)

	def DecodeDirectives(self):
		for directive in self.DirectivesLines:
			split = directive.String.split("=")
			split = [piece.strip() for piece in split]
			if len(split) != 2:
				Common.Error(directive, "Wrong syntax for directive")
			else:
				tempDirective = split[1]
				for prevDirective, value in self.Directives.iteritems():
					extracted = [piece for piece in re.split("[^a-zA-Z0-9_]", tempDirective)] # Split the instruction by spaces, commas, and brackets
					if prevDirective in extracted:
						tempDirective = tempDirective.replace(prevDirective, value)
				self.Directives[split[0]] = tempDirective.strip() if tempDirective.startswith('R') else "0x"+Common.ExprToHexString(tempDirective.strip(),directive)

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

class Parser:

	def __init__(self, assemblyFilePath, addressWidth, canInclude = False, label=None):
		self.AssemblyFilePath = assemblyFilePath
		self.Assembly = Assembly(addressWidth)
		self.AddressWidth = addressWidth
		self.CanInclude = canInclude
		self.Label = label
		self.LabelTable = {}
		self.IncludeFiles = []
		self.IncludeParsers = []

	def Assemble(self):
		for instruction in self.Assembly.Instructions:
			instruction.Assemble()
		for parser in self.IncludeParsers:
			for instruction in parser.Assembly.Instructions:
				instruction.Assemble()

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
		allParsers = []
		allParsers.append(self)
		for parser in self.IncludeParsers:
			allParsers.append(parser)
		for parser in allParsers:
			if parser.Label != None and parser.Assembly.Instructions:
				lines.append(Mif.MifLine(comment="----- %s -----" % parser.Label.String))
			for instruction in parser.Assembly.Instructions:
				data = Common.NumToHexString(int(instruction.MachineCode, 2), 8)
				comment = instruction.Line.String.strip().replace('\t',' ')
				lines.append(Mif.MifLine(data=data, comment=comment, instruction=instruction))
		return lines

	def GetConstantsData(self):
		lines = []
		addresses = {}
		for address, data in self.Assembly.Constants.iteritems():
			if address in addresses.keys():
				if addresses[address] == data[0]:
					continue
				else:
					Common.Error(data[1], "Duplicate constant found at address: 0x%s. Address already assigned to: 0x%s" % (address, addresses[address]))
			lines.append(Mif.MifLine(data=data[0], address=address, comment="%s:%s" % (data[1].FileName, data[1].Number)))
			addresses[address] = data[0]
		for parser in self.IncludeParsers:
			for address, data in parser.Assembly.Constants.iteritems():
				if address in addresses.keys():
					if addresses[address] == data[0]:
						continue
					else:
						Common.Error(data[1], "Duplicate constant found at address: 0x%s. Address already assigned to: 0x%s" % (address, addresses[address]))
				lines.append(Mif.MifLine(data=data[0], address=address, comment="%s:%s" % (data[1].FileName, data[1].Number)))
				addresses[address] = data[0]
		return lines

	@staticmethod
	def GetInterruptVectorTable():
		lines = []
		for num, dest in Assembly.InterruptVectorTable.iteritems():
			dest = Common.NumToHexString(dest, 8)
			lines.append(Mif.MifLine(address=Assembly.VectorTableStartAddress+num, data=dest, comment="ISR_%i" % num))
		return lines

	def MergeIncludes(self):
		addressCounter = len(self.Assembly.Instructions)
		for parser in self.IncludeParsers:
			label = parser.Label.String.split()[0]
			if label in self.LabelTable.keys():
				Common.Error(parser.Label, "Duplicate include label: %s" % parser.Label.String)
			self.LabelTable[label] = addressCounter
			addressCounter = parser.ResolveAddresses(startAddress=addressCounter)
			parser.SetLabelAddresses()
		self.ResolveAddresses()
		self.SetLabelAddresses()

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
		category = Common.Enum("Directives", "Constants", "Code", "Includes")
		myCategory = None

		for line in self.Assembly.WithoutComments:
			if line.String.strip() == ".directives":
				myCategory = category.Directives
			elif line.String.strip() == ".constants":
				myCategory = category.Constants
			elif line.String.strip() == ".code":
				myCategory = category.Code
			elif line.String.strip() == ".includes":
				if not self.CanInclude:
					Common.Error(line, "Cannot recursively include files")
				myCategory = category.Includes
			elif line.String.startswith('.end'):
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
				elif myCategory == category.Includes:
					if not line in self.IncludeFiles:
						self.IncludeFiles.append(line)
				else:
					Common.Error(line, "Line \"%s\" belongs to unknown section" % line.String)

	def Parse(self):
		self.FileToLines(self.AssemblyFilePath)
		self.Assembly.WithoutComments = self.RemoveComments()
		self.Separate()
		self.Assembly.Decode()
		if self.CanInclude:
			self.ParseIncludes()
			self.MergeIncludes()
			self.Assemble()

	def ParseIncludes(self):
		for include in self.IncludeFiles:
			split = include.String.split()
			if len(split) != 3:
				Common.Error(constant, "Wrong syntax for include")
			filePath = os.path.abspath(split[2])
			if not os.path.isfile(filePath):
				Common.Error(include, "Cannot find file: %s" % filePath)
			includeParser = Parser(filePath, self.AddressWidth, label=include)
			includeParser.Parse()
			self.IncludeParsers.append(includeParser)

	def ResolveAddresses(self, startAddress = 0):
		addressCounter = startAddress
		for instruction in self.Assembly.Instructions:
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
					if instruction.Label in self.LabelTable.keys():
						Common.Error(instruction.Line, "Found previous declaration of label: %s" % instruction.Label)
					self.LabelTable[instruction.Label] = addressCounter
			addressCounter += 1
		return addressCounter

	def SetLabelAddresses(self):
		for instruction in self.Assembly.Instructions:
			if instruction.NeedsLabelAddress:
				if instruction.LabelOperand in self.LabelTable.keys():
					instruction.Address = self.LabelTable[instruction.LabelOperand]
				else:
					Common.Error(instruction.Line, "Could not find destination label for: %s" % instruction.LabelOperand)
		return self.Assembly.Instructions
