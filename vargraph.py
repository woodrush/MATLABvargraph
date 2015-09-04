# coding: UTF-8
from sys import argv
from utils import argparse, evalOrLoadPickle
from parser import searchvars
from termcolor import colored
from os import listdir
import re

def printUsage():
	print "Usage:"
	print "    python vargraph.py [-r <vars> ...] [-s <vars> ...]"
	print "                       [-m <vars> ...] [-m2 <vars> ...] [-m3 <vars> ...]"
	print "                       [-rf <filename>] [-sf <filename>]"
	print "                       [-mf <filename>] [-mf2 <filename>] [-mf3 <filename>]"
	print "                       [-d <depth>]"
	print "                       [-dot] [-force] [-traceback] [-rall]"
	print "    -r, -rf, -rall: Specify the variables to track dependencies"
	print "                      -rall specifies all variables in project"
	print "                      Input files should be space-delimited"
	print "    -s, -sf:        Specify variables to be skipped in the output"
	print "    -m*, -mf*:      Specify variables to be marked in the output or DOT file"
	print "    -d:             Specify the maximum depth of the graph"
	print "                      Use a sufficiently large number to draw all dependencies"
	print "    -dot:           Output a Dot file (./vargraph.dot)"
	print "    -force:         Force evaluation (specify after updating file)"
	print "    -traceback:     Trace the dependency graph backwards"
	print ""
	print "Typical usage example:"
	print "    python vargraph.py -r myvar myvar2"
	print "    python vargraph.py -d 10 -rf nan_vars.txt -mf nan_vars.txt -sf real_vars.txt -dot"
	print ""
	print "Notes:"
	print "    Please place all *.m files in the same directory as this file on use."

#======================================================================
# Parser
#======================================================================
def matchIdentifierIter(string):
	for x in re.finditer(r"[a-zA-Z_$][a-zA-Z_0-9$]*", string):
		yield x.group()

def extractRelevantLine(searchfile):
	with open(searchfile + ".m", "r") as f:
		isCommentBlock = False
		acceptedline = ""
		for line in f:
			if isCommentBlock:
				if line.strip() == "%}":
					isCommentBlock = False
			elif not isCommentBlock:
				if line.strip() == "%{":
					isCommentBlock = True
				else:
					line = re.sub("%.*$", "", line).strip().lstrip()
					if line.endswith("..."):
						acceptedline += line[:-3]
					else:
						yield acceptedline + line
						acceptedline = ""

def extractRelevantExprList(searchfile):
	for line in extractRelevantLine(searchfile):
		# If line is a function decleration
		if re.search(r"^function\s", line):
			line = line.replace(r"^function\s", "", 1)
			if "=" in line:
				splitted = line.split("=")
				outvars = list(matchIdentifierIter(splitted[0]))
				temp = list(matchIdentifierIter(splitted[1]))
				funcname = temp[0]
				invars = temp[1:]
			else:
				temp = list(matchIdentifierIter(line))
				funcname = temp[0]
				invars = temp[1:] if temp[1:] else []
				outvars = []
			invars = invars if invars else []
			outvars = outvars if outvars else []
			yield {"type":"funcdecl","funcname":funcname,"invars":invars,"outvars":outvars}
		# If line is a for loop
		elif re.search(r"^for\s", line):
			varlist = [x for x in matchIdentifierIter(line) if x != "for"]
			assignee = [varlist[0]]
			sourceexprs = varlist[1:]
			yield {"type":"forassignment","assignee":assignee,"sourceexprs":sourceexprs}
		# If line is a global variable declaration
		elif re.search(r"^global\s", line):
			varlist = list(matchIdentifierIter(line))
			yield {"type":"globaldecl","varlist":varlist}
		# If line is an assignment
		elif "=" in line and re.search("[^~=><]=[^=]", line):
			varlist = list(matchIdentifierIter(line))
			assignee = [varlist[0]]
			sourceexprs = varlist[1:]
			yield {"type":"assignment","assignee":assignee,"sourceexprs":sourceexprs}

#======================================================================
# Creating the graph
#======================================================================
def searchvars():
	def addEdge(g,s,t=None):
		if g.get(s) == None:
			g[s] = []
		if t != None and t not in g[s]:
			g[s].append(t)
	def addIfNew(l,varname):
		if varname not in l:
			l.append(varname)
	files = [f[:-2] for f in listdir('.') if f.endswith('.m')]
	graph = {}
	invgraph = {}
	sourcefile = {}
	forvars = []
	funcInOutVars2 = []
	for searchfile in files:
		numcalls = 0
		isFunction = False
		funcInOutVars = []
		globalvars = []
		def decorateFuncInOutVars(varname):
			return '__' + searchfile + '__' + varname if isFunction and varname in funcInOutVars else varname
		for expr in extractRelevantExprList(searchfile):
			# Function decleration
			if expr["type"] == "funcdecl":
				isFunction = True
				funcInOutVars = expr["invars"] + expr["outvars"]
				funcInOutVars2 += map(decorateFuncInOutVars,funcInOutVars)
			elif expr["type"] == "globaldecl":
				globalvars += expr["varlist"]
				for tvar in expr["varlist"]:
					addEdge(sourcefile,tvar,searchfile)
					addEdge(graph,tvar)
					addEdge(invgraph,tvar)
			# Assignment
			else:				
				if expr["type"] == "forassignment":
					map(lambda x:addIfNew(forvars,x), map(decorateFuncInOutVars, expr["assignee"]))
				for tvar in map(decorateFuncInOutVars,expr["assignee"]):
					if not(isFunction and tvar not in globalvars):
						addEdge(sourcefile,tvar,searchfile)
						addEdge(graph,tvar)
						addEdge(invgraph,tvar)
						for svar in map(decorateFuncInOutVars,expr["sourceexprs"]):
							if not(isFunction and tvar not in globalvars):
								addEdge(graph,svar,tvar)
								addEdge(invgraph,svar)
								addEdge(sourcefile,svar)
								addEdge(invgraph,tvar,svar)
	return (files,graph,invgraph,sourcefile,forvars,funcInOutVars2)

#======================================================================
# Preparations
#======================================================================
# Parse args
(rootvars, skipvars, markvars, markvars2, markvars3, printmode, forcesearch, maxdepth, tracebackmode, rAllmode) = argparse(argv[1:])
# Get the graph
(files,graph,invgraph,sourcefile,forvars,funcInOutVars) = evalOrLoadPickle("graph.pkl", searchvars, forcesearch)

# Draw a graph with opposite edges
if tracebackmode:
	graph, invgraph = invgraph, graph
if rAllmode:
	rootvars = graph.keys()
if not rootvars:
	printUsage()

#======================================================================
# Draw the graph
#======================================================================
def drawDot():
	drawn = dict.fromkeys(graph.iterkeys(), False)
	def draw(targetvar,myfile,depth):
		if targetvar in markvars:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#ff0000\"]\n")
		elif targetvar in markvars2:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#ff22ff\"]\n")
		elif targetvar in markvars3:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#22ff22\"]\n")
		elif targetvar in funcInOutVars:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#0000ff\"]\n")
		elif targetvar in files:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#ffff00\"]\n")
		elif targetvar in forvars:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#00ffff\"]\n")
		elif not invgraph[targetvar]:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#ff00ff\"]\n")
		else:
			myfile.write("\"" + targetvar + "\" [style = filled, fillcolor = \"#ffffff\"]\n")
		if not drawn[targetvar]:
			drawn[targetvar] = True
			if depth < maxdepth:
				for sourcevar in invgraph[targetvar]:
					if targetvar not in skipvars:
						draw(sourcevar,myfile,depth+1)
						if not tracebackmode:
							myfile.write("\"" + sourcevar + "\"" + "->" + "\"" + targetvar + "\"\n")
						else:
							myfile.write("\"" + targetvar + "\"" + "->" + "\"" + sourcevar + "\"\n")
	with open("./vargraph.dot", "w") as myfile:
		myfile.write("digraph vargraph {\nlayout=dot\nnode [shape = circle, style = filled, margin = 0];\n")
		for f in rootvars:
			draw(f,myfile,0)
		myfile.write("}")

def drawtext():
	def colorvarslist(varlist, default="white"):
		def decorateVar(a):
			colors = ["white","white", "white", default, "magenta", "yellow", "cyan", "white", "blue"]
			varlabel =  0 if a in markvars else \
						1 if a in markvars2 else \
						2 if a in markvars3 else \
						8 if a in funcInOutVars else \
						6 if a in forvars else \
						5 if a in files else \
						7 if a in skipvars else \
						4 if not invgraph[a] else \
						3
			if varlabel == 5:
				vartext = colored(a, colors[varlabel], attrs=['dark'])
			elif varlabel == 0:
				vartext = colored(a, colors[varlabel], 'on_red',attrs=['bold'])
			elif varlabel == 1:
				vartext = colored(a, colors[varlabel], 'on_magenta',attrs=['bold'])
			elif varlabel == 2:
				vartext = colored(a, colors[varlabel], 'on_green',attrs=['bold'])
			else:
				vartext = colored(a, colors[varlabel])
			return (a,vartext,varlabel)
		return sorted(map(decorateVar, varlist), key=lambda x: x[2], reverse=False)
	def colorvars(varlist_in, default="white"):
		varlist = colorvarslist(varlist_in, default)
		if varlist:
			return reduce(lambda x,y: x + y[1] + " ", varlist, "")
		else:
			return ""
	pastvarlist = []
	varlist = rootvars
	for depth in range(maxdepth+1):
		nextvarlist = []
		for (v,vtext,label) in colorvarslist(varlist):
			if v not in pastvarlist and v not in skipvars:
				pastvarlist.append(v)
				sourcetext = (reduce(lambda x,y: y + ".m " + x, sourcefile[v], "") if sourcefile[v] else " ")[:-1]
				if not (invgraph.get(v) == None):
					print "        "*depth + colorvars([v]) + ("-> " if tracebackmode else "<- ") \
					+ colored("(" + sourcetext +"): ", "green") \
					+ colorvars(invgraph[v])
					nextvarlist += invgraph[v]
		varlist = nextvarlist

drawtext()
if printmode == "dot":
	drawDot()
