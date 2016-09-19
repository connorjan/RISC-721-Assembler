import Common

class MifLine():

	def __init__(self, data=None, address = None, comment = "", instruction = None):
		self.Address = address
		self.Data = data
		self.Comment = comment
		self.Instruction = instruction

	def __str__(self):
		string = ""
		if self.Address != None:
			if type(self.Address) is str:
				string += self.Address.replace("0x",'').zfill(4)
			else:
				string += Common.NumToHexString(self.Address, 4)
	 	if self.Data != None:
	 		string += " : %s;" % self.Data.zfill(8)
	 	if self.Comment:
	 		string += " %% %s %%" % self.Comment

	 	return string

	def __repr__(self):
	 	return str(self)

class Mif():

	def __init__(self, output, width, address, headers = []):
		self.OutputFile = output
		self.Width = width
		self.Address = address
		self.Depth = 2**address
		#self.DataRadix = dataRadix
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
				_file.write("-- Assembled for RISC_721 by Connor Goldberg\n")

				for line in self.Headers:
					_file.write("-- %s\n" % line)

				_file.write("\nWIDTH = %s;\n" % str(self.Width))
				_file.write("DEPTH = %s;\n" % str(self.Depth)) #TODO: Check to see if number of instts is less than depth
				_file.write("ADDRESS_RADIX = HEX;\n")
				_file.write("DATA_RADIX = %s;\n" % str(self.DataRadix))
				_file.write("\nCONTENT BEGIN\n")
				_file.write("\n")

				addressCounter = 0
				for mifLine in self.Data:
					if mifLine.Data == None:
						_file.write(str(mifLine).strip()+'\n')
					elif mifLine.Address != None:
						_file.write(str(mifLine)+'\n')
						addressCounter+=1
					else:
						mifLine.Address = addressCounter
						_file.write(str(mifLine)+'\n')
						addressCounter+=1

				_file.write("\nEND;\n")