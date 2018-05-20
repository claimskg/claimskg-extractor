# -*- coding: utf-8 -*-
import sys,getopt,datetime,codecs
import claimextractor as ce


if sys.version_info[0] < 3:
    import got
else:
    import got3 as got

def main(argv):

	if len(argv) == 0:
		print('You must pass some parameters. Use \"-h\" to help.')
		return

	if len(argv) == 1 and argv[0] == '-h':
		f = open('exporter_help_text.txt', 'r')
		print f.read()
		f.close()

		return

	try:
		opts, args = getopt.getopt(argv, "", ("website=", "since=", "until=", "maxclaims=", "output="))

		options={} 
		outputFileName = "output_got.csv"

		for opt,arg in opts:
			if opt == '--website':
				options['website'] = arg

			elif opt == '--since':
				options['since']= arg

			elif opt == '--until':
				options['until'] = arg

			elif opt == '--maxclaims':
				options['maxclaims'] = int(arg)

			elif opt == '--output':
				outputFileName = arg
				
		

		ce.get_claims(options['website'])

	except arg:
		print('Arguments parser error, try -h' + arg)
	finally:
		outputFile.close()
		print('Done. Output file generated "%s".' % outputFileName)

if __name__ == '__main__':
	main(sys.argv[1:])
