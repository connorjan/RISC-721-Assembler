from ast import literal_eval
import os
import struct
import sys

def Enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def Error(line, errorMsg = ""):
	if type(line) is str:
		print line
	elif line == None:
		print errorMsg
	else:
		print "Error in %s on line %s:\n\t%s\n%s" % (line.FileName, line.Number, line.String, errorMsg)
	sys.exit(1)

LegalChars = "0123456789xXaAbBcCdDeEfF() *^+-/.%<>&|~\t"
def Evaluate(expr, line=None, canReturnFloat=False):
	try:
		expr = expr.replace('^',"**")
		for char in expr:
			if char not in LegalChars:
				return expr
		res = eval(expr)
		if type(res) is float:
			if canReturnFloat:
				return res
			else:
				return int(res)
		elif type(res) is not int and type(res) is not long:
			newRes = int(round(res))
			warnMsg = "Converted %s %s to %s" % (type(res), res, newRes)
			Warn(line, warnMsg)
			return newRes
		else:
			return res
	except Exception as e:
		Error(line, "Invalid expression: %s" % expr)

def ExprToHexString(expr, line=None, padding=0):
	expr = expr.strip()
	if expr.startswith(".float(") and expr.endswith(")"):
		expr = expr[expr.find("(")+1:expr.rfind(")")]
		return FloatToHexString(Evaluate(expr,line=line,canReturnFloat=True), line)
	else:
		return NumToHexString(Evaluate(expr,line), line=line, padding=padding)

def SliceBits(num, msb, lsb=None):
	"""
	Slice bits from an integer from the msb to the lsb (inclusive) and 0-indexed
	If no lsb is provided it will only grab the one bit at the msb specified
	num - the number
	msb - the most significant bit to keep
	lsb - the least significant bit to keep
	ex. SliceBits(0xF000, 15, 12) = 0xF
	ex. SliceBits(0x7800, 14, 11) = 0xF
	"""
	width = (msb-lsb+1) if lsb is not None else 1
	return (((2**(width))-1 << msb-width+1) & num) >> msb-width+1

def FileToList(filePath):
	if os.path.isfile(filePath):
		with open(filePath) as _file:
			return [line.strip() for line in _file]
	else: 
		return []

def FloatToHexString(f, line=None):
	try:
		return str(hex(struct.unpack('<I', struct.pack('<f', float(f)))[0]))[2:].upper().strip('L')
	except Exception as e:
		Error(line, "Invalid expression")

def NumToBinaryString(number, padding = 0):
	formatter = "{0:0%sb}" % padding
	return formatter.format(number)

def NumToHexString(number, padding = 0, line=None):
	try:
		formatter = "{0:0%sx}" % padding
		return formatter.format(number).upper()
	except Exception:
		Error(line, "Invalid expression")

def SecondsToStr(t):
    return "%d:%02d:%02d.%03d" % \
        reduce(lambda ll,b : divmod(ll[0],b) + ll[1:],
            [(t*1000,),1000,60,60])

def Warn(line, errorMsg = ""):
	if type(line) is str or line == None:
		print line
	else:
		print "Warning in %s on line %s:\n\t%s\n%s" % (line.FileName, line.Number, line.String, errorMsg)
