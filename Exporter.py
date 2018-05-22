# -*- coding: utf-8 -*-
import sys,getopt,datetime,codecs
sys.path.append('ce')

import claimextractor as ce
import Criteria 




# if sys.version_info[0] < 3:
#     import got
# else:
#     import got3 as got

def main(argv):
	options={} 
	criteria = Criteria.Criteria()
	criteria.setOutput("output_got.csv")

	if len(argv) == 0:
		print('You must pass some parameters. Use \"-h\" to help.')
		return

	if len(argv) == 1 and argv[0] == '-h':
		f = open('exporter_help_text.txt', 'r')
		print f.read()
		f.close()

		return

	try:
		opts, args = getopt.getopt(argv, "", ("website=", "since=", "until=", "maxclaims=", "output=","language="))

		
		
		for opt,arg in opts:
			if opt == '--website':
				criteria.website= arg

			elif opt == '--since':
				criteria.since= arg

			elif opt == '--until':
				criteria.until = arg

			elif opt == '--maxclaims':
				criteria.maxClaims = int(arg)

			elif opt == '--language':
				criteria.language = arg

			elif opt == '--output':
				criteria.output = arg

	except:
		print('Arguments parser error, try -h')
	
	ce.get_claims(criteria)
	print('Done. Output file generated "%s".' % criteria.output)

if __name__ == '__main__':
	main(sys.argv[1:])
