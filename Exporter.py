# -*- coding: utf-8 -*-
import getopt
import sys

sys.path.append('claim_extractor')

from claim_extractor import claimextractor as ce
from claim_extractor import Configuration


# if sys.version_info[0] < 3:
#     import got
# else:
#     import got3 as got

def main(argv):
    options = {}
    criteria = Configuration()
    criteria.setOutput("output_got.csv")

    if len(argv) == 0:
        print('You must pass some parameters. Use \"-h\" to help.')
        return

    if len(argv) == 1 and argv[0] == '-h':
        f = open('exporter_help_text.txt', 'r')
        print(f.read())
        f.close()

        return

    try:
        opts, args = getopt.getopt(argv, "", ("website=", "maxclaims="))

        for opt, arg in opts:
            if opt == '--website':
                criteria.website = arg

            if opt == '--maxclaims':
                criteria.maxClaims = int(arg)

    except:
        print('Arguments parser error, try -h')
        exit()

    ce.get_claims(criteria)
    print(('Done. Output file generated "%s".' % criteria.output))


if __name__ == '__main__':
    main(sys.argv[1:])
