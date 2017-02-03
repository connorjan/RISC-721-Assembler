import Common

class MifLine(object):

	Comment = {
				"altera" : "--",
				"cadence" : "//"
	}

	def __init__(self, data=None, address = None, comment = "", instruction = None):
		self.Address = address
		self.Data = data
		self.Comment = comment
		self.Instruction = instruction

	def Altera(self):
		string = ""
		if self.Address is not None:
			if type(self.Address) is str:
				string += self.Address.replace("0x",'').zfill(4)
			else:
				string += Common.NumToHexString(self.Address, 4)
		if self.Data != None:
			string += " : %s;" % self.Data.zfill(8)
		if self.Comment:
			string += " %% %s %%" % self.Comment

		return string

	def Cadence(self):
		string = "@"
		if self.Address is not None:
			if type(self.Address) is str:
				string += self.Address.replace("0x",'').zfill(4)
			else:
				string += Common.NumToHexString(self.Address, 4)
		if self.Data != None:
			string += "    {}".format(self.Data.zfill(8))
		if self.Comment:
			string += " // {}".format(self.Comment)

		return string

	def ToString(self, _format):
		if _format == "altera":
			return self.Altera()
		elif _format == "cadence":
			return self.Cadence()
		else:
			Common.Error(errorMsg="Invalid format")

	def __str__(self):
		return None

class Mif(object):

	def __init__(self, _format, output, width, address, headers = []):
		self.Format = _format
		self.OutputFile = output
		self.Width = width
		self.Address = address
		self.Depth = 2**address
		self.DataRadix = "HEX"
		self.Headers = headers
		self.Data = []

	def AddData(self, data):
		if data:
			self.Data += data
		return self

	def Write(self):
		if self.Data:
			with open(self.OutputFile, "w+") as _file:
				_file.seek(0)
				_file.truncate() # Clears out the file if it exists
				_file.write("{} Assembled for RISC_721 by Connor Goldberg\n".format(MifLine.Comment[self.Format]))

				for line in self.Headers:
					_file.write("{} {}\n".format(MifLine.Comment[self.Format], line))

				if self.Format == "altera":
					_file.write("\nWIDTH = %s;\n" % str(self.Width))
					_file.write("DEPTH = %s;\n" % str(self.Depth)) #TODO: Check to see if number of instts is less than depth
					_file.write("ADDRESS_RADIX = HEX;\n")
					_file.write("DATA_RADIX = %s;\n" % str(self.DataRadix))
					_file.write("\nCONTENT BEGIN\n")
				
				_file.write("\n")

				addressCounter = 0
				for mifLine in self.Data:
					if mifLine.Data is None:
						_file.write(mifLine.ToString(self.Format).strip()+'\n')
					elif mifLine.Address is not None:
						_file.write(mifLine.ToString(self.Format)+'\n')
						addressCounter+=1
					else:
						mifLine.Address = addressCounter
						_file.write(mifLine.ToString(self.Format)+'\n')
						addressCounter+=1
				
				if self.Format == "altera":
					_file.write("\nEND;\n")
