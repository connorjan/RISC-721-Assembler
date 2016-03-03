import os
import sys

def Enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def Error(line, errorMsg = ""):
	if type(line) is str:
		print line
	else:
		print "Error in %s on line %s:\n\t%s\n%s" % (line.FileName, line.Number, line.String, errorMsg)
	sys.exit(1)

def FileToList(filePath):
	if os.path.isfile(filePath):
		with open(filePath) as _file:
			return [line.strip() for line in _file]
	else: 
		return []

def NumToBinaryString(number, padding = 0):
	formatter = "{0:0%sb}" % padding
	return formatter.format(number)

def NumToHexString(number, padding = 0):
	formatter = "{0:0%sx}" % padding
	return formatter.format(number).upper()

def SecondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],
            [(t*1000,),1000,60,60])