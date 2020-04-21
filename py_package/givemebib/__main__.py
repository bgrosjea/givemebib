#!/usr/bin/env python
import sys, os, re, time, random
from pathlib import Path

errorlog = Path('givemebib.log').open(mode = 'w')  
if hasattr(sys, 'frozen') : 
    if getattr(sys, 'frozen') and hasattr(sys, '_MEIPASS'): # running in a PyInstaller bundle
        application_path = Path(os.path.dirname(sys.executable))
else: #running in a normal Python process : python3 script.py arg1 arg2
    application_path = Path(os.path.dirname(__file__))

abbrev_dat = Path(application_path)/'journal_abbreviations.dat'

if not abbrev_dat.exists() : 
    err = ('journal_abbreviations.dat not found at location: ' + str(abbrev_dat.absolute()))
    errorlog.write(err)
    sys.exit(err + '\nCANCELLING JOB')

try : 
    exclusion_file = Path(application_path)/'givemebib.ini'
except : 
    err = ('givemebib.ini not found at location: ', str(exclusion_file))
    errorlog.write(err)
    sys.exit(err + '\nCANCELLING JOB')
exclusion_list = []
with exclusion_file.open() as inputfile : 
    for line in inputfile : 
        line = line.strip().replace('\t', ' ')
        while '  ' in line : 
            line = line.replace('  ', ' ')
        if not line.startswith('#') : 
            for field in line.split(' ') : 
                exclusion_list.append(field)

from givemebib.functions import *




def main() : 
    # Start of INPUT PARSING
    input_target = False
    try : 
        target = sys.argv[1]
    except : 
        target = input("""Current directory is {} \nPlease provide target (.pdf, directory containing .pdf, .bib, doi, 
    google scholar query or a file with a list of doi or a list of scholar queries):   """.format(str(Path.cwd()))).strip()
    input_target = True
    try : 
        abbrev = int(sys.argv[-1])
    except : 
        abbrev = int(input('Do you wish the output .bib with full (0) or abbreviated (1) journal names \n(0 or 1)>   ').strip())

    possible_types = ['dir', 'pdf', 'doi', 'doi_list', 'bib', 'query', 'query_list']
    doi_str = "\\bdoi:10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|\\bhttp[s]*://[dx/]*doi.org/10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|10\.(\\d)+/([\\w\\.\\-\\_()])+\\b"
    doi_re = re.compile(doi_str)

    # Start of Target detection 
    target_type = ''
    if Path(target).is_dir(): 
        target_type = 'dir'
        if target == './' or target == '.' : 
            target = Path.cwd()
        else : 
            target = Path(target)
        pdf_list= []
        ispdf = False 
        for file in target.iterdir() : 
            if file.suffix == '.pdf' :
                ispdf = True
                pdf_list.append(file)
        if ispdf : 
            print('TARGET has been understood as a DIRECTORY WITH PDF FILES. ')
        else : 
            sys.exit("""TARGET has been understood as a DIRECTORY but NO PDF FILES were found (extension .pdf is required). 
    CANCELLING JOB""")
    elif Path(target).is_file() : 
        target = Path(target) 
        if target.suffix == '.pdf' : 
            target_type = 'pdf'
            pdf_file = target
            print('TARGET has been understood as a SINGLE PDF FILE. ')
        elif target.suffix == '.bib' :
            target_type = 'bib'
            bib = target.open().read() 
            print('TARGET has been understood as a BIB FILE. ')
        else : 
            openfile = target.open().read() 
            inputfile = openfile.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ')
            while '  ' in inputfile : 
                inputfile = inputfile.replace('  ', ' ')
            inputfile = inputfile.strip().split(' ')
            isdoi = True
            for item in inputfile : 
                if not doi_re.search(item) : 
                    isdoi = False
            if isdoi : 
                target_type = 'doi_list'
                doi_list = inputfile
                print('TARGET has been understood as a LIST OF DOIs. ')
            else : 
                target_type = 'query_list'
                inputfile = openfile.split('\n')
                query_list = []
                for line in inputfile : 
                    line = line.strip()
                    if line != '' :
                        query_list.append(line.strip())
                print('TARGET has been understood as a LIST OF GOOGLE SCHOLAR QUERIES. ')
    elif doi_re.search(target) :
        doi = doi_re.search(target).group(0)
        target_type = 'doi'
        print('TARGET has been understood as a SINGLE DOI. ')
    elif len(sys.argv[1:-1]) > 0 :
        target_type = 'query'
        target = ' '.join(sys.argv[1:-1])
        query = target
        print('TARGET has been understood as a SINGLE GOOGLE SCHOLAR QUERY. ')
    elif input_target and target.strip().replace(' ', '') != '' : 
        target_type = 'query'
        query = target
        print('TARGET has been understood as a SINGLE GOOGLE SCHOLAR QUERY. ')
    print('TARGET = ', target)
    print('abbrev = ', abbrev)

    if target_type == '' :
        sys.exit("""TARGET not understood. It has NOT been identified as:
        _ a directory with .pdf files
        _ a pdf file (must end by .pdf)
        _ a file containing a list of DOIs (DOIs must be separated by spaces, tabulations or new lines)
        _ a single DOI (doi syntax: 10.digits/string)
        _ a bib file (must end by .bib)
    CANCELLING JOB""")
    # End of target detection

    if abbrev == 0 : 
        print("\nbib2reformat > Will replace journal abbreviations by full names, ", end = '')
    elif abbrev == 1 :
        print("\nbib2reformat > Will replace journal titles by their abbreviations, ", end = '')
    else : 
        sys.exit("""Last argument can only be 0 or 1. Argument passed: {}
    CANCELLING JOB""".format(abbrev))
    print("using journal abbreviations .dat file: ==> " + str(abbrev_dat) + " <==")
    for key in exclusion_list : 
        print("bib2reformat > Will also remove {} data.".format(key))
    print("bib2reformat > Fields to ommit can be customised in file: ==> " + str(exclusion_file) + " <==")

    # End of INPUT PARSING

    # Start of APPLICATION
    missed = [[], []]
    if target_type == 'doi' : 
        try : 
            bib = doi2bib(doi)
        except : 
            sys.exit('The doi you entered ' + doi + ' is likely incorrect as it was not recognized by http://api.crossref.org/\nCANCELLING JOB')
        bib, missed = bib2reformat(bib, abbrev, exclusion_list)
        filename = savenonamebib(bib, Path('./')) 
        print('Saving doi {} into file:\n{}'.format(doi, str(Path(filename).absolute())))

    elif target_type == 'query' : 
        try : 
            doi = scholarquery2doi(query)
        except : 
            sys.exit('scholarquery2doi > no result for query (IP might be blocked after multiple queries): {}\nCANCELLING JOB'.format(query))
        try : 
            bib = doi2bib(doi)
        except : 
            sys.exit('doi provided by scholarquery2doi gave no result:\nquery: {}\ndoi:{}\nCANCELLING JOB'.format(query, doi))
        bib, missed = bib2reformat(bib, abbrev, exclusion_list)
        filename = savenonamebib(bib, Path('./')) 
        print('Saving doi {}\nObtained as first google scholar result from query: "{}"\nInto file:\n{}'.format(doi, query, str(Path(filename).absolute())))

    elif target_type == 'query_list' : 
        missing_list = []
        bib_dir = target.parent/Path('single_bibs')
        Path.mkdir(bib_dir, exist_ok = True) 
        fullbibname = target.with_suffix('.full.bib')
        if fullbibname.exists() : 
            answer = input('To export all DOIs into a single .bib file, ' + fullbibname.name + ' already exists, do you wish to overwrite it? \n(y/desired file name)> ')
            if answer != 'y' :
                fullbibname = target.parent/answer 
        fullbibfile = fullbibname.open(mode = 'w') 
        print('Single .bib from the provided list of dois can be found in ' + str(bib_dir))
        for query in query_list : 
            sleeptime = 3 + random.uniform(1, 4)
            print('Script pausing {} seconds not to be blocked by Google Scholar'.format(round(sleeptime, 3)))
            time.sleep(sleeptime)
            isdoi = False
            isbib = False
            msg = ''
            try : 
                doi = scholarquery2doi(query)
                isdoi = True
            except : 
                err = 'scholarquery2doi > no result for query (IP might be blocked after multiple queries): {}'.format(query)
                msg = [query, 'no doi found by scholarquery2doi']
                missing_list.append(msg)
                errorlog.write('\n' + err)
                print(err)
            if isdoi : 
                try : 
                    bib = doi2bib(doi)
                    isbib = True
                except : 
                    err = 'doi provided by scholarquery2doi gave no result:\nquery: {}\ndoi:{}'.format(query, doi)
                    msg = [query, doi]
                    missing_list.append(msg)
                    errorlog.write('\n' + err)
                if isbib : 
                    bib, missed_tuple = bib2reformat(bib, abbrev, exclusion_list)
                    if len(missed_tuple[0]) >0 : 
                        missed[0].append(missed_tuple[0][0])
                        missed[1].append(missed_tuple[1][0])
                    fullbibfile.write('\n\n' + bib)
                    bibfile = savenonamebib(bib, bib_dir) 
        fullbibfile.close()
        if len(missing_list) != 0 : 
            msg = '\nThe following queries gave no result: '
            for i, missing in enumerate(missing_list) : 
                msg += '\nquery:   "{}"    doi: {}'.format(missing[0], missing[1])
            errorlog.write('\n' + msg)
        msg += """\n\n All bib in a single .bib file: {}
    Each single .bib files in: {}""".format(str(fullbibname.absolute()), str(bib_dir.absolute()))
        print(msg)

    elif target_type == 'doi_list' :
        missing_list = []
        bib_dir = target.parent/Path('single_bibs')
        Path.mkdir(bib_dir, exist_ok = True) 
        fullbibname = target.with_suffix('.full.bib')
        if fullbibname.exists() : 
            answer = input('To export all DOIs into a single .bib file, ' + fullbibname.name + ' already exists, do you wish to overwrite it? \n(y/desired file name)> ')
            if answer != 'y' :
                fullbibname = target.parent/answer 
        fullbibfile = fullbibname.open(mode = 'w') 
        print('Single .bib from the provided list of dois can be found in ' + str(bib_dir))
        for doi in doi_list : 
            isbib = False
            try : 
                bib = doi2bib(doi)
                isbib = True
            except : 
                missing_list.append(doi)
            if isbib : 
                bib, missed_tuple = bib2reformat(bib, abbrev, exclusion_list)
                if len(missed_tuple[0]) >0 : 
                    missed[0].append(missed_tuple[0][0])
                    missed[1].append(missed_tuple[1][0])
                fullbibfile.write('\n\n' + bib)
                bibfile = savenonamebib(bib, bib_dir) 
        fullbibfile.close()
        if len(missing_list) != 0 : 
            msg = '\nThe following DOIs gave no result: '
            for missing in missing_list : 
                msg += '\n' + missing
            errorlog.write(msg)
        msg += """\n All bib in a single .bib file: {}
    Each single .bib files in: {}""".format(str(fullbibname.absolute()), str(bib_dir.absolute()))
        print(msg)
            
    elif target_type == 'bib' : 
        bib, missed_tuple = bib2reformat(bib, abbrev, exclusion_list)
        if len(missed_tuple[0]) >0 : 
            for i, article in enumerate(missed_tuple[0]) : 
                missed[0].append(article)
                missed[1].append(missed_tuple[1][i])
        bibname = target.with_suffix('.reformat.bib')
        if bibname.exists() : 
            answer = input(bibname.name + ' already exists, do you wish to overwrite it? \n(y/desired file name)> ')
            if answer != 'y' : 
                bibname = bibname.parent/answer
        with bibname.open(mode = 'w') as bibfile : 
            bibfile.write(bib)
            
    elif target_type == 'pdf' : 
        isdoi = False
        isbib = False
        try : 
            doi = pdf2doi(pdf_file)
            stock_doi = doi
            isdoi = True
        except : 
            err = 'pdf2doi > Failure to read file or find a doi for ' +  pdf_file.name
            errorlog.write('\n' + err)
            sys.exit(err + '\nCANCELLING JOB')
        if isdoi : 
            i = 0
            page = ''
            temp_doi = doi
            while not isbib: 
                if i > 0:
                    temp_doi = doi[:-i]
                    if temp_doi[-1] == '/' :
                        break
                try: 
                    bib = doi2bib(temp_doi)
                    isbib = True
                    break
                except: 
                    i += 1
            if temp_doi != doi and isbib: 
                err =  """For file: {}   with detected doi: {}    the following doi worked: {}    
                Please check it refers to the right article""".format(pdf_file.name, stock_doi, temp_doi)
                errorlog.write(err)
                print(err)
            elif not isbib : 
                err = 'Failure on file: {}   detected doi: {}    last tested doi: {}    No tested doi gave a result'.format(pdf_file.name, doi, temp_doi) 
                errorlog.write(err)
                sys.exit(err + '\nCANCELLING JOB')
        if isbib : 
            bib, missed_tuple = bib2reformat(bib, abbrev, exclusion_list) 
            if len(missed_tuple[0]) >0 :
                missed[0].append(missed_tuple[0][0]) 
                missed[1].append(missed_tuple[1][0]) 
            bibname = pdf_file.with_suffix('.bib') 
            if bibname.exists() :
                answer = input(bibname.name + ' already exists, do you wish to overwrite it? \n(y/desired file name)> ') 
                if answer != 'y' : 
                    bibname  = bibname.parent/answer 
            with bibname.open(mode = 'w') as bibfile : 
                bibfile.write(bib)
            
    elif target_type == 'dir' : 
        error_list = []
        doi_fail_list = []
        read_fail_list = []
        bib_dir = target/'single_bibs' 
        Path.mkdir(bib_dir, exist_ok = True)
        fullbibname = target/Path(target.name).with_suffix('.full.bib')

        if fullbibname.exists() :
            answer = input('To export all bibs into a single .bib file, ' + fullbibname.name + ' already exists, do you wish to overwrite it? \n(y/desired file name)> ')
            if answer != 'y' :
                fullbibname = target.parent/answer 
        fullbibfile = fullbibname.open(mode = 'w') 
        for pdf_file in pdf_list : 
            pdfname = pdf_file.name 
            isdoi = False
            isbib = False
            try : 
                doi = pdf2doi(pdf_file)
                isdoi = True
            except : 
                err = 'pdf2doi > Failure to read file or find a doi for ' +  pdfname
                errorlog.write(err)
                read_fail_list.append([pdfname, 'pdf2doi failure: reading error or no DOI detected'])
            if isdoi : 
                error = ['', '', '']
                i = 0
                isbib = False
                page = ''
                while not isbib: 
                    temp_doi = doi
                    if i > 0:
                        temp_doi = doi[:-i]
                        if temp_doi[-1] == '/' :
                            break
                    try: 
                        bib = doi2bib(temp_doi)
                        isbib = True
                        break
                    except: 
                        i += 1
                if isbib and temp_doi != doi : 
                    err = [pdfname, doi, temp_doi]
                    error_list.append(err)
                elif not isbib : 
                    err = 'Failure on file: {}   detected doi: {}    last tested doi: {}    No tested doi gave a result'.format(pdfname, doi, temp_doi)
                    doi_fail_list.append([pdfname, doi, temp_doi])
            if isbib : 
                bib, missed_tuple = bib2reformat(bib, abbrev, exclusion_list)
                if len(missed_tuple[0]) >0 :
                    missed[0].append(missed_tuple[0][0]) 
                    missed[1].append(missed_tuple[1][0]) 
                bibname = bib_dir/Path(pdf_file.name).with_suffix('.bib') 
                if bibname.exists() : 
                    answer = input(bibname.name + ' already exists, do you wish to overwrite it? \n(y/desired file name)> ') 
                    if answer != 'y' : 
                        bibname = bibname.parent/answer
                with bibname.open(mode = 'w') as bibfile : 
                    bibfile.write(bib)
                fullbibfile.write('\n\n' + bib)
        msg = """\nAll bib in a single .bib file: {}
        Each single .bib files in: {}""".format(str(fullbibname.absolute()), str(bib_dir.absolute()))
        print(msg)
        if len(error_list) > 0 : 
            msg = '\n\nFor the following files, only a modified DOI worked, PLEASE CHECK IT REFERS TO THE RIGHT ARTICLE:'
            errorlog.write(msg)
            print(msg)
            for err in error_list:
                msg = 'File: {}   detected doi: {}   working doi: {}'.format(err[0], err[1], err[2])
                errorlog.write('\n' + msg)
                print(msg)
        if len(read_fail_list) > 0 or len(doi_fail_list) > 0 : 
            msg = '\n\nCOMPLETE FAILURE for the following .pdf files. DOI or BIB to be provided manually.'
            errorlog.write(msg)
            for err in read_fail_list : 
                msg = 'File: {}   {}'.format(err[0], err[1])
                errorlog.write('\n' + msg)
                print(msg)
            for err in doi_fail_list : 
                msg = 'File: {}   detected doi: {}    Last tested doi: {}    NO DOI WORKED'.format(err[0], err[1], err[2])
                errorlog.write('\n' + msg)
                print(msg)
        fullbibfile.close()

    missed_article = missed[0]
    missed_journal = missed[1]
    if len(missed_article) > 0 : 
        err = '\n\nMISSING abbreviation data for the following articles. Please check if journal names are correctly formatted.'
        print(err)
        errorlog.write(err)
        for i, article in enumerate(missed_article) : 
            journal = missed_journal[i]
            err = 'Article: {}    journal name or abbreviation: {}'.format(article, journal)
            print(err)
            errorlog.write('\n' + err)

    # End of APPLICATION

if __name__ == "__main__":
    print(__name__)
    main()
errorlog.close()

