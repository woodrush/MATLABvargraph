# coding: UTF-8
import os
import pickle

def evalOrLoadPickle(path,defaultfunc,force):
	def picklesave(obj,filename):
		with open(filename, 'wb') as output:
			pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)
	if force:
		print "Forcing evaluation"
	else:
		if os.path.isfile(path):
			with open(path, "rb") as f:
				try:
					return pickle.load(f)
				except StandardError:
					pass
		print "No pickle cache found: evaluating function"
	ret = defaultfunc()
	picklesave(ret,path)
	return ret

def argparse(args):
	rootvars = []
	skipvars = []
	markvars = []
	markvars2 = []
	markvars3 = []
	printmode = "textlinear"
	forcesearch = False
	maxdepth = 2
	tracebackmode = False
	rAllmode = False
	currentcommand = "-r"
	for a in args:
		if a.startswith("-"):
			if a == "-dot":
				printmode = "dot"
			elif a == "-traceback":
				tracebackmode = True
			elif a == "-force":
				forcesearch = True
			elif a == "-rall":
				rAllmode = True
			else:
				currentcommand = a
		else:
			if currentcommand == "-r":
				rootvars.append(a)
			elif currentcommand == "-s":
				skipvars.append(a)
			elif currentcommand == "-m":
				markvars.append(a)
			elif currentcommand == "-m2":
				markvars2.append(a)
			elif currentcommand == "-m3":
				markvars3.append(a)
			elif currentcommand == "-rf":
				with open(a, "r") as f:
					for line in f:
						rootvars += line.split(' ')
			elif currentcommand == "-sf":
				with open(a, "r") as f:
					for line in f:
						skipvars += line.split(' ')
			elif currentcommand == "-mf":
				with open(a, "r") as f:
					for line in f:
						markvars += line.split(' ')
			elif currentcommand == "-mf2":
				with open(a, "r") as f:
					for line in f:
						markvars2 += line.split(' ')
			elif currentcommand == "-mf3":
				with open(a, "r") as f:
					for line in f:
						markvars3 += line.split(' ')
			elif currentcommand == "-d":
				maxdepth = int(a)
				currentcommand = "-r"
	return (rootvars, skipvars, markvars, markvars2, markvars3, printmode, forcesearch, maxdepth, tracebackmode, rAllmode)
