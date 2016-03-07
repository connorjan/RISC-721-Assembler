#!/usr/bin/env python
import argparse
import os
from time import clock

import Common
import Mif
import Parser

"""
Title: Assembler for RISC521
Author: Connor Goldberg
"""

def main(args):
	start = clock()

	assemblyFile = args["assembly-file"]
	output = args["output"]
	if output == None:
		programOutput = os.path.join(os.path.split(os.path.abspath(assemblyFile))[0],os.path.splitext(os.path.basename(assemblyFile))[0]+".mif")
		dataOutput = os.path.join(os.path.split(os.path.abspath(assemblyFile))[0],os.path.splitext(os.path.basename(assemblyFile))[0]+"_DM.mif")
	elif not output.endswith(".mif"):
		programOutput = output + ".mif"
		dataOutput =  output + "_DM.mif"

	programMif = Mif.Mif(programOutput, args["width"], args["depth"], ["Program memory for: %s" % assemblyFile])
	dataMif = Mif.Mif(dataOutput, args["width"], args["depth"], ["Data memory for: %s" % assemblyFile])

	myParser = Parser.Parser(assemblyFile)	
	myParser.Parse()

	Parser.Assembly.ResolveAddresses(myParser.Assembly.Instructions, 0)

	programMif.AddData(myParser.GetAssemblyData()).Write()
	dataMif.AddData(Parser.Parser.GetInterruptVectorTable()).AddData(myParser.GetConstantsData()).Write()
	
	end = clock()
	
	print "Successfully assembled %s into %s and %s" % (assemblyFile, programOutput, dataOutput)
	print "Time elapsed: %s ms" % str(round(float(end-start)*1000,3))

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description="Assembler for RISC_721 by Connor Goldberg")
	parser.add_argument("assembly-file", help="File to be assembled")
	parser.add_argument("-o", "--output", metavar="out-file", type=str, help="The path of the MIF file")
	parser.add_argument("-d", "--depth", metavar="depth", type=int, help="The depth of the output file", default=65536)
	parser.add_argument("-w", "--width", metavar="width", type=int, help="The width of instruction words", default=32)
	args = vars(parser.parse_args())
	main(args)