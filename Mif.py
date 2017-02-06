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

	def GetAddressAsInt(self):
		try:
			if type(self.Address) is str:
				return int(self.Address, 16)
			else:
				return self.Address
		except Exception as e:
			print e
			raise e

	def Altera(self):
		string = ""
		if self.Address is not None:
			if type(self.Address) is str:
				string += self.Address.replace("0x",'').zfill(4)
			else:
				string += Common.NumToHexString(self.Address, 4)
		if self.Data is not None:
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
		if self.Data is not None:
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

	def __init__(self, _format, output, width, address, headers = [], writeZeros=False):
		self.Format = _format
		self.OutputFile = output
		self.Width = width
		self.Address = address
		self.Depth = 2**address
		self.DataRadix = "HEX"
		self.Headers = headers
		self.Data = []
		self.WriteZeros = writeZeros
		self.AddressesWritten = set()

	def AddData(self, data):
		if data:
			self.Data += data
		return self

	def AddAddress(self, address):
		if address in self.AddressesWritten:
			Common.Error(errorMsg="Address already written to: {}".format(address))
		else:
			self.AddressesWritten.add(address)

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
					if mifLine.Data is None and mifLine.Address is None:
						# This is just a comment
						_file.write(mifLine.ToString(self.Format).strip()+'\n')
					elif mifLine.Address is not None:
						# If there is data and an address
						_file.write(mifLine.ToString(self.Format)+'\n')
						self.AddAddress(mifLine.GetAddressAsInt())
						#addressCounter+=1
					else:
						mifLine.Address = addressCounter
						_file.write(mifLine.ToString(self.Format)+'\n')
						self.AddAddress(mifLine.GetAddressAsInt())
						addressCounter+=1
				
				if self.WriteZeros:
					for a in range(0, self.Depth):
						if a not in self.AddressesWritten:
							_file.write(MifLine(data="0", address=a).ToString(self.Format)+'\n')

				if self.Format == "altera":
					_file.write("\nEND;\n")
