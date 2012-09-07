#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
    \file mendeley2bibtex.py
    \author François Bianco, University of Geneva – francois.bianco@unige.ch
    \date 2012.09


    \mainpage Mendeley To BibTeX convertor

    This script converts Mendeley SQlite database to BibTeX file.


    \section Infos

     mendeley2bibtex.py was written by François Bianco, University of Geneva
– francois.bianco@unige.ch in order to get a correct conversion of Mendely
database to BibTeX not provided by the closed source Mendeley Desktop software.

    First locate your database. On Linux systems it is:
    
ls ~/.local/share/data/Mendeley\ Ltd./Mendeley\
Desktop/your@email.com@www.mendeley.com.sqlite

    Make a copy of this file, as we assume no responsability for loss of data.

    Then run mendeley2bibtex.py on your file:


    \section Copyright

    Copyright © 2012 François Bianco, University of Geneva –
francois.bianco@unige.ch

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    See COPYING file for the full license.

    \section Updates

    2012.09:
        First Version

"""

import sys
from optparse import OptionParser
import sqlite3

version = '0.01'

def dict_factory(cursor, row):
    """A class to use the SQLite row as dict for string formatting"""
    d = {}
    for idx, col in enumerate(cursor.description):
        if row[idx]:
            d[col[0]] = row[idx]
        else:
            d[col[0]] = ''
    return d

def convert(db_name, bibtex_file=sys.stdout, quiet=False):
    """Converts Mendely SQlite database to BibTeX file
    @param db_name The Mendeley SQlite file
    @param bibtex_file The BibTeX file to output the bibliography, if not
supplied the output is written to the system standard stdout.
    @param quiet If true do not show warnings and errors
    """
    
    db = sqlite3.connect(db_name)
    c = db.cursor()
    #c.row_factory = sqlite3.Row # CANNOT be used with unicode string formatting
                                 # since it expect str indexes, and we are using
                                 # unicode string... grrr... ascii is not dead
    c.row_factory = dict_factory # allows to use row (entry) as a dict with
                                 # unicode keys.
                                 
    if sys.stdout != bibtex_file:
        f = open(bibtex_file,'w')
        f.write("""This file was generated automatically by Mendeley To
BibTeX python script.\n\n""")
    else:
        f = bibtex_file

    for entry in c.execute('''
    SELECT
        D.id,
        D.citationKey,
        D.title,
        D.type,
        D.doi,
        D.publisher,
        D.publication,
        D.volume,
        D.issue,
        D.month,
        D.year,
        D.pages,
        F.localUrl
    FROM Documents D
    JOIN DocumentCanonicalIds DCI
        ON D.id = DCI.documentId
    JOIN DocumentFiles DF
        ON D.id = DF.documentId
    JOIN Files F
        ON F.hash = DF.hash
    WHERE D.confirmed = "true"
    GROUP BY D.citationKey
    ORDER BY D.citationKey
    ;'''):

        c2 = db.cursor()
        c2.execute('''
    SELECT lastName, firstNames
    FROM DocumentContributors
    WHERE documentId = ?
    ORDER BY id''', (entry['id'],))
        authors_list = c2.fetchall()
        authors = []
        for author in authors_list:
            authors.append(', '.join(author))
        entry['authors'] = ' and '.join(authors)


        # If you need to add more templates:
        #    all types of templates are available at
        #    http://www.cs.vassar.edu/people/priestdo/tips/bibtex
        if "JournalArticle" == entry['type']:
            formatted_entry = u'''
@article{{{entry[citationKey]},
    author    = "{entry[authors]}",
    title     = "{entry[title]}",
    journal   = "{entry[publication]}",
    number    = "{entry[issue]}",
    volume    = "{entry[volume]}",
    pages     = "{entry[pages]}",
    year      = "{entry[year]}",
    doi       = "{entry[doi]}",
    localfile = "{entry[localUrl]}"
}}'''.format(entry=entry)


        elif "Book" == entry['type']:
            formatted_entry = u'''
@book{{{entry[citationKey]},
    author    = "{entry[authors]}",
    title     = "{entry[title]}",
    publisher = "{entry[publisher]}",
    year      = "{entry[year]}",
    volume    = "{entry[volume]}",
    doi       = "{entry[doi]}",
    localfile = "{entry[localUrl]}"
}}'''.format(entry=entry)


        else:
            if not quiet:
                print u'''Unhandled entry type {0}, please add your own
template.'''.format(entry['type'])
            continue
        
        f.write(formatted_entry.encode("UTF-8"))

    if sys.stdout != bibtex_file:
        f.close()


def main() :
    """Set this script some command line options. See usage."""

    global version

    parser = OptionParser(usage='''
  usage: %prog [mendeley.sqlite] -o [out.bib]''',version='%prog '+version)

    parser.add_option('-q', '--quiet', action='store_true', default=False,
                dest='quiet', help='Do not display information.')
    parser.add_option("-o", "--output", dest="bibtex_file", default=sys.stdout,
                help="BibTeX file name, else output will be printed to stdout")

    (options, args) = parser.parse_args()

    if not args :
        parser.error('''No file specified''')

    db_name = args

    convert(db_name[0], options.bibtex_file, options.quiet)


if __name__ == "__main__":
    try :
        main()
    except (KeyboardInterrupt) :
        print "Interrupted by user."
