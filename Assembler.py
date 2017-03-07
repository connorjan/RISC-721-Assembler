#!/usr/bin/env python

import argparse
import os
import time

import Common
import Mif
import Parser

"""
Title: Assembler for RISC_721
Author: Connor Goldberg
"""

def main(args):

	start = time.clock()

	assemblyFile = args["assembly-file"]
	output = args["output"]
	if output == None:
		programOutput = os.path.join(os.path.split(os.path.abspath(assemblyFile))[0],os.path.splitext(os.path.basename(assemblyFile))[0]+".mif")
		dataOutput = os.path.join(os.path.split(os.path.abspath(assemblyFile))[0],os.path.splitext(os.path.basename(assemblyFile))[0]+"_dm.mif")
	elif not output.endswith(".mif"):
		programOutput = output + ".mif"
		dataOutput =  output + "_dm.mif"
	else:
		programOutput = output
		split = os.path.splitext(output)
		dataOutput = split[0] + "_dm"
		if len(split) == 2:
			dataOutput = dataOutput + split[1]
		else:
			dataOutput = dataOutput + ".mif"

	stuffMem = 0
	if args["stuff"] is not None:
		try:
			if args["stuff"].upper().startswith("0X"):
				stuffMem = int(args["stuff"], 16)
			else:
				stuffMem = int(args["stuff"])
		except Exception as e:
			Common.Error("Cannot stuff with: {}".format(args["stuff"]))

	programMif = Mif.Mif(_format=args["format"], output=programOutput, width=args["width"], address=args["address_width"], headers=["Program memory for: %s" % assemblyFile], stuffWith=stuffMem)
	dataMif = Mif.Mif(_format=args["format"], output=dataOutput, width=args["width"], address=args["address_width"], headers=["Data memory for: %s" % assemblyFile], stuffWith=stuffMem)

	myParser = Parser.Parser(assemblyFile, args["address_width"], canInclude=True)	
	myParser.Parse()

	programMif.AddData(myParser.GetAssemblyData()).Write()
	dataMif.AddData(Parser.Parser.GetInterruptVectorTable()).AddData(myParser.GetConstantsData()).Write()
	
	end = time.clock()
	
	print "Successfully assembled {} into {}{}".format(assemblyFile, programOutput, " and "+dataOutput if dataMif.Data else '')
	print "Time elapsed: %s ms" % str(round(float(end-start)*1000,3))
	print "Completed on %s at %s" % (time.strftime("%m/%d/%Y"), time.strftime("%I:%M:%S"))

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description="Assembler for RISC_721 by Connor Goldberg")
	parser.add_argument("assembly-file", help="File to be assembled")
	parser.add_argument("-o", "--output", metavar="out-file", type=str, help="The path of the MIF file")
	parser.add_argument("-a", "--address_width", metavar="address-width", type=int, help="The width of the address bus", default=16)
	parser.add_argument("-w", "--width", metavar="width", type=int, help="The width of instruction words", default=32)
	parser.add_argument("-f", "--format", metavar="format", type=str, help="The output format of the assembled mif file", choices=["altera","cadence"], default="cadence")
	parser.add_argument("-s", "--stuff", metavar="stuff", type=str, help="Specify if uninitialized values should be exlicitly written")

	args = vars(parser.parse_args())
	main(args)
