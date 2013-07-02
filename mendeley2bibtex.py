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

    Then run mendeley2bibtex.py on your file with

        ./mendeley2bibtex.py -o mendeley.bib mendeley.sqlite


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
import re

version = '0.01'

def clean_char(entry):
    """A helper function to convert special characters to LaTeX characters"""

    # List of char and replacement, add your own list below
    char_to_replace = {
        # LaTeX special char
        '&':'\&',
        # UTF8 not understood by inputenc
        u'–':'--', # utf8 2014, special dash
        u'—':'--', # utf8 2013, special dash
        u'∕':'/',  # utf8 2215, math division
        u'κ':'k', # Greek kappa
        u'×':'x', # times
        }

    # Which field shall we check and convert
    entry_key=['publisher','publication','title']

    for k in entry_key:
        for char, repl_char in char_to_replace.iteritems():
            entry[k] = entry[k].replace(char,repl_char)

#from string import capwords
def capwords(s):
    """Reimplement a custom capitalize word function which keeps words
unchanged except the first letter (useful for chemical compounds and
special abreviation with capital letter within the word) and which capitalizes
both words of hyphenated words."""

    for sep in (' ', '-'):
       s = sep.join( x[0].capitalize()+x[1:] \
                for x in s.split(sep) if x )

    ## Expanded version for tests/debugging ;-)
    #for sep in (' ', '-'):
        #new_w = []
        #for w in s.split(sep):
            #if not w:
                #continue
            #new_w.append( w[0].capitalize()+w[1:] )
        #s = sep.join(new_w)
    return s

def capitalize_title(entry):
    """Helper function to convert paper title to camel case text, according
    to ACS format : no capital on article and prepositions, hyphenated text
have both words capitalized (except for verbs).

    BUG : Even hyphenated verbs are capitalized in this version.
          No possibility to distinguished between As for arsenic and the article
          Or In for indium or in(side)

    """

    title = capwords(entry['title'])

    word_not_captitalized = ['of','an','on','at', 'to', 'for', 'from', 'in','as',
                             'by','a','with','and','the','in'] # ,'as'
    for w in word_not_captitalized:
        title = title.replace(' '+w.capitalize()+' ',' '+w+' ')
        title = title.replace('-'+w.capitalize()+'-','-'+w+'-')

    title = title.replace('as Atomic', 'As Atomic')
    entry['title'] = title


def dict_factory(cursor, row):
    """A function to use the SQLite row as dict for string formatting"""
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
    LEFT JOIN DocumentCanonicalIds DCI
        ON D.id = DCI.documentId
    LEFT JOIN DocumentFiles DF
        ON D.id = DF.documentId
    LEFT JOIN Files F
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

        #capitalize_title(entry)
        clean_char(entry)

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


        elif "ConferenceProceedings" == entry['type']:
            formatted_entry = u'''
@proceedings{{{entry[citationKey]},
    author    = "{entry[authors]}",
    title     = "{entry[title]}",
    publisher = "{entry[publisher]}",
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
  usage: %prog [-o out.bib] mendeley.sqlite''',version='%prog '+version)

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
