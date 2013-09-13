#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import logging
import traceback
from optparse import OptionParser
import gentoopm
from gentoopm.portagepm.depend import PortageConditionalUseDep

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
import portman #@UnresolvedImport

__all__ = []


class Dependency(object):
	
	def __init__(self, package, dependencies):
		self.package = package
		self.dependencies = dependencies
	
	def flatten(self, l=None):
		l = l or []
		
		for p in self.dependencies:
			p_deps = p.flatten(l)
			p_deps.append(p)
			
		
		return l
	
	def __str__(self):
		return str(self.package)
	

def test_deps(src, dst, pkg):
	dep_list = []
	checked_deps = []

	for t in (pkg.run_dependencies, pkg.build_dependencies):
		for dep in t:
			if isinstance(dep, PortageConditionalUseDep):
				dep_list.extend(dep._deps)
			else:
				dep_list.append(dep)

	l = []
	for dep in dep_list:
		if dep in checked_deps:
			continue
		checked_deps.append(dep)

		src_matches = src.filter(dep)
		dst_matches = dst.filter(dep)
		
		if dst_matches and not src_matches:
			# dependency is already in tree
			continue

		best = src_matches.best
		#print "%sMove %s" % (" " * indent, str(best))
		#l.append(test_deps(src, dst, best))
		l.append(test_deps(src, dst, best))
	return Dependency(pkg, l)


def build_tree(cpv, src_tree, dst_tree):
	pm = gentoopm.get_package_manager()
	
	src = pm.repositories[src_tree]
	dst = pm.repositories[dst_tree]
	
	for src_cpv in src.filter(cpv):
		yield (src_cpv, test_deps(src, dst, src_cpv))

def main(argv=None):
	'''Command line options.'''
	
	program_version = "v%s" % portman.VERSION
	version_string = '%%prog %s' % (program_version, )
	usage = '''usage: [options] (print|graph) cpv'''
	license = "Copyright 2013 Johann Schmitz. Licensed under the GPL-2"
	
	if argv is None:
		argv = sys.argv[1:]

	try:
		# setup option parser
		parser = OptionParser(version=version_string, epilog="", description=license, usage=usage)
		parser.add_option("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %default]")
		parser.add_option("-s", "--source-tree", dest="src", help="Source tree")
		parser.add_option("-d", "--destination-tree", dest="dest", help="Destination tree [default: %default]", default="gentoo")
		
		# process options
		(opts, args) = parser.parse_args(argv)
		
		if not opts.verbose:
			opts.verbose = 0

		if opts.verbose > 5:
			opts.verbose = 5 
		
		logging.basicConfig(
			level = 50 - (int(opts.verbose) * 10),
			format = '%(asctime)s %(levelname)-8s %(message)s',
		)

		if not args or not opts.src or (len(args) == 2 and args[0] not in ['print', 'graph']):
			parser.print_help()
		
		cpv = args[len(args)-1] 
		action = "print" if len(args) == 1 else args[0]

		if action == "print":
			for src_cpv, t in build_tree(cpv, opts.src, opts.dest):
				
				def print_deptree(t, indent=0):
					print "%s%s" % (" " * indent, t.package)
					
					for d in t.dependencies:
						print_deptree(d, indent+1)
					

				print_deptree(t)
				
				
#				print "\nPort the following packages to the tree (in order):"
				#for i, item in enumerate(t.flatten()):
					#print "%2i. %s" % (i+1, item)

				
#				print "Tree for %s:" % src_cpv
#				def print_deptree(t, indent=0):
#					for pkg, deps in t:
#						print "%s%s" % (" " * indent, str(pkg))
#						print_deptree(deps, indent+2)
#				
#				print_deptree([t])
#
#				print "\nPort the following packages to the tree (in order):"
#				for i, item in enumerate(flatten_tree([t])):
#					print "%2i. %s" % (i+1, item)
		else:
			pass

	except Exception, e:
		print e
		print traceback.format_exc()
		return 2


if __name__ == "__main__":
	sys.exit(main())