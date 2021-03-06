#!/usr/bin/env python

import argparse
import os
import sys
import time

import Common
import Mif
import Parser

"""
Title: Disassembler for RISC_721
Author: Connor Goldberg
"""

def main(args):

	start = time.clock()

	mifFile = args["mif-file"]
	output = args["output"]
	if output == None:
		programOutput = os.path.join(os.path.split(os.path.abspath(mifFile))[0],os.path.splitext(os.path.basename(mifFile))[0]+".asm")
	elif not output.endswith(".asm"):
		programOutput = output + ".asm"
	else:
		programOutput = output
		split = os.path.splitext(output)

	myParser = Parser.DisassemblyParser(mifFilePath=mifFile, mifFormat=args["format"], width=args["width"], memoryWidth=args["memory_width"], debug=args["debug"])
	myParser.Parse()

	myParser.Disassembly.Write(programOutput, [" ".join(sys.argv)])
	
	end = time.clock()
	
	print "Successfully disassembled {} into {}".format(mifFile, programOutput)
	print "Time elapsed: %s ms" % str(round(float(end-start)*1000,3))
	print "Completed on %s at %s" % (time.strftime("%m/%d/%Y"), time.strftime("%I:%M:%S"))

if __name__ == "__main__":
	
	parser = argparse.ArgumentParser(description="Assembler for RISC_721 by Connor Goldberg")
	parser.add_argument("mif-file", help="File to be disassembled")
	parser.add_argument("-o", "--output", metavar="out-file", type=str, help="The path of the ASM file")
	parser.add_argument("-m", "--memory_width", metavar="memory_width", type=int, help="The width of a word in memory in bits (default = 8)", default=8)
	parser.add_argument("-w", "--width", metavar="width", type=int, help="The width of instruction words in bits (default = 32)", default=32)
	parser.add_argument("-f", "--format", metavar="format", type=str, help="The input format of the assembled mif file", choices=["altera","cadence"], default="cadence")
	parser.add_argument("-d", "--debug", action="store_true", help="Output debug information")

	args = vars(parser.parse_args())
	main(args)
