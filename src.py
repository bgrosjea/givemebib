__version__ = '1.0.0'
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

def scholarquery2doi(query) : 
    """Given a query, returns the doi of the first result of a Google Scholar search.
    Examples: 
        doi = scholarquery2doi('author:Smith 2020 graphene ~device -nanotube')
        doi = scholarquery2doi('Versatile electrification of two-dimensional nanomaterials in water')"""
    import re, sys
    try : 
        import mechanize
    except : 
        sys.exit("""mechanize is not installed, please run in terminal
        pip install mechanize
    CANCELLING JOB""")
    doi_str = "\\bdoi:10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|\\bhttp[s]*://[dx/]*doi.org/10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|10\.(\\d)+/([\\w\\.\\-\\_()])+\\b"
    doi_re = re.compile(doi_str)
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.addheaders = [('User-Agent', 'Mozilla/5.0')]
    br.open('https://scholar.google.com/')
    br.select_form(nr = 0)
    br['as_q'] = query
    sub = br.submit()
    url_list = [link.absolute_url for link in br.links()]
    for i, url in enumerate(url_list) : 
        if 'google' not in url and 'http' in url: 
            msg = '\nscholarquery2doi > query: "{}" \nFirst Google Scholar match: {}\n'.format(query, url)
            print(msg)
            break
    response = br.open(url)
    response = str(response.read())
    br.close()
    doi = doi_re.search(response).group(0)
    return(doi)

def pdfminer2doi(pdf_file) : 
    """Given a .pdf file of a publication, tries to return the corresponding doi. 
    This is a complementary method to the one using PyPDF2. It is better to use pdf2doi(pdf_file) as it has both methods implemented."""
    import re, sys, time, random
    try :
        from pdfminer.pdfparser import PDFParser
        from pdfminer.pdfdocument import PDFDocument
        from pdfminer.pdfpage import PDFPage
        from pdfminer.pdfpage import PDFTextExtractionNotAllowed
        from pdfminer.pdfinterp import PDFResourceManager
        from pdfminer.pdfinterp import PDFPageInterpreter
        from pdfminer.pdfdevice import PDFDevice
        from pdfminer.layout import LAParams
        from pdfminer.converter import PDFPageAggregator
    except : 
        sys.exit("""pdfminer is not installed or only the python2 version, please run in terminal: 
        pip install pdfminer.six
    CANCELLING JOB""")
    from pathlib import Path
    if type(pdf_file) == str : 
        pdf_file = Path(pdf_file)
    doi_str = "\\bdoi:10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|\\bhttp[s]*://[dx/]*doi.org/10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|10\.(\\d)+/([\\w\\.\\-\\_()])+\\b"
    doi_re = re.compile(doi_str)
    pdf = pdf_file.open(mode = 'rb')
    parser = PDFParser(pdf)
    document = PDFDocument(parser)
    if not document.is_extractable:
        raise PDFTextExtractionNotAllowed
    rsrcmgr = PDFResourceManager()
    laparams = LAParams()
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    fig_list = []
    method = 'pdfminer'
    for i, page in enumerate(PDFPage.create_pages(document)):
        interpreter.process_page(page)
        layout = device.get_result()
        isdoi = False
        for item in layout:
            try : 
                txt = item.get_text()
                fig_re = re.compile('\\bFigure[ ]*[\d]+[.]+|\\bFig.[ ]*[\d]+[.]+|\\bFIGURE[ ]*[\d]+[.]+|\\bFIG.[ ]*[\d]+[.]+')
                if fig_re.search(txt) : 
                    fig_str = txt.split(fig_re.search(txt).group(0))[-1]
                    fig_list.append(fig_str.replace('\n', ' ').strip())
                if doi_re.search(txt) :
                    doi = doi_re.search(txt).group(0)
                    isdoi = True
                    break
            except : 
                pass
        if isdoi : 
            break
    if not isdoi : # trying using figure captions as Google Scholar queries
        print('pdfminer2doi > trying figure captions with scholarquery2doi')
        for fig_str in fig_list : 
            try : 
                sleeptime = 3 + random.uniform(1, 4)
                print('Script pausing {} seconds not to be blocked by Google Scholar'.format(round(sleeptime, 3)))
                time.sleep(sleeptime)
                doi = scholarquery2doi(fig_str)
                isdoi = True
                method = 'scholarquery@pdfminer' # NEXT: fix this method as it quickly gets the IP blocked by Google Scholar
            except : 
                pass
    if isdoi : 
        return(doi, method)
    pdf.close()
    
def pdf2doi(pdf_file) :
    """Finds doi from the pdf of a publication (pdf_file = pdf filepath)
    \nThe doi detected can contain additional characters""" 
    import re, sys
    try : 
        from PyPDF2 import PdfFileReader
    except : 
        sys.exit("""PyPDF2 is not installed, please run in terminal
        pip install PyPDF2
    CANCELLING JOB""")
    from pathlib import Path 
    if type(pdf_file) == str : 
        pdf_file = Path(pdf_file)
    doi_str = "\\bdoi:10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|\\bhttp[s]*://[dx/]*doi.org/10\.(\\d)+/([\\w\\.\\-\\_()])+\\b|10\.(\\d)+/([\\w\\.\\-\\_()])+\\b"
    doi_re = re.compile(doi_str)
    pdf_input = PdfFileReader(pdf_file.open(mode = 'rb'))
    npage = pdf_input.getNumPages()
    info = pdf_input.documentInfo
    doi_read = False
    method = ''
    for key in info : #trying directly in pdf informations
        text = info[key]
        match = doi_re.search(text)
        try : 
            doi = match.group(0)
            doi_read = True
            method = 'PyPDF2-info'
        except: 
            pass
    ipage = 0
    while not doi_read and ipage < npage : # trying within the pdf pages
        try : 
            text = pdf_input.getPage(ipage).extractText()
            match = doi_re.search(text)
        except : 
            pass
        try : 
            doi = match.group(0)
            doi_read = True
            method = 'PyPDF2-page{}'.format(ipage)
        except: 
            ipage += 1
    if not doi_read : 
        try : 
            print('pdf2doi > trying with pdfminer2doi')
            doi, method = pdfminer2doi(pdf_file) #trying with pdfminer as pdf reading module
            doi_read = True
        except : 
            pass
    if method == 'scholarquery@pdfminer' : 
        print('pdf2doi > PDF: {} ==> relied on scholarquery, possibly found the doi of another article'.format(pdf_file.parts[-1]))
    elif method == '' : 
        print('pdf2doi > PDF: {} No method provided doi (IP might be blocked by Google Scholar after multiple queries) '.format(pdf_file.parts[-1]))
    print('pdf2doi (with {})> PDF: {} ==> DOI: {}'.format(method, pdf_file.parts[-1], doi))
    return(doi)

def doi2bib(doi):
    """Given a doi, returns a clean bib downloaded from http://api.crossref.org/"""
    from urllib.request import urlopen
    url_test = False
    page = ''
    try: 
        page = urlopen('http://api.crossref.org/works/' + doi + '/transform/application/x-bibtex')
        url_test = True
    except: 
        url_test = False
    bib = str(page.read())
    if bib[:2] == "b'" : 
        bib = bib[2:]
    if bib[-1] == "'" :
        bib = bib[:-1]
    if bib[:2] == 'b"' : 
        bib = bib[2:]
    if bib[-1] == '"' :
        bib = bib[:-1]
    bib = bib.encode('utf_8').decode('unicode_escape')
    return(bib)

def pdf2bib(pdf_file) : 
    """Given the pdf of a publication, downloads a clean corresponding bib from http://api.crossref.org/
    \nInterfaces pdf2doi and doi2bib. pdf2doi can provide incorrect doi with additional characters. 
    The doi is tested while removing characters until finding the correct doi, 
    but sometimes the starting string given by pdf2doi if any is completely incorrect.
    \nReturns as well error messages linked with the reading of doi as a list : 
    \n[pdf_file, last tested doi, string]."""
    from pathlib import Path
    if type(pdf_file) == str : 
        pdf_file = Path(pdf_file)
    doi = pdf2doi(pdf_file)
    error = ['', '', '']
    i = 0
    url_test = False
    page = ''
    while not url_test: 
        temp_doi = doi
        if i > 0:
            temp_doi = doi[:-i]
            if temp_doi[-1] == '/' :
                break
        try: 
            bib = doi2bib(temp_doi)
            url_test = True
            break
        except: 
            i += 1
    if temp_doi != doi : 
        error = [pdf_file.split('/')[-1], doi, temp_doi]
    elif not url_test : 
        error = [pdf_file.split('/')[-1], doi, 'No DOI tested gave a result.']
    return(bib, error)

def pdf2bibfile(pdf_file):
    """Given the filepath to a file.pdf, returns a bib in file.bib"""
    import sys
    from pathlib import Path
    if type(pdf_file) == str : 
        pdf_file = Path(pdf_file)
    if not pdf_file.endswith('.pdf') : 
        sys.exit('pdf2bibfile > Provided file does not have the correct .pdf extension. \nCANCELLING JOB')
    bibfile = (pdf_file.parent/pdf_file.name).with_suffix('.bib')
    with bibfile.open(mode =  'w') as output : 
        output.write( pdf2bib(pdf_file)[0] )
    print('pdf2bibfile > PDF: {} bib info exported into BIB: {}'.format(pdf_file.parts[-1], bibfile.parts[-1])) 

def bib2reformat(bib, abbrev, exclusion_list):
    """Given a bib string returns a reformated bib string. bib2reformat(bib string, 0 or 1, list of info field to exclude e.g. url)
    0: non abbreviated journal names
    1: abbreviated journal names
    exclusion_list: ['doi', 'url', 'page', ...]
    \nReformatting can include abbreviation of journal names, 
    deletion of fields such as url, doi etc. 
    It can also reverse abbreviated journal names to full names."""
    import sys, os
    from pathlib import Path
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

    def cleanline(line) :
        line = line.strip()
        line = line.replace('\t', ' ')
        while '  ' in line :
            line = line.replace('  ', ' ')
        return(line)

    # Part 1 : reading journal abbreviations .dat file
    journal_dat = {}
    journal2abbrev = {}
    case_corresp = {}
    with abbrev_dat.open() as inputfile:  
        iline = 0
        for line in inputfile : 
            iline += 1 
            if not line.startswith('#') : 
                line = cleanline(line)
                if 'XXX<>XXX' in line: 
                    tab = line.split('XXX<>XXX')
                    title = tab[0].strip().replace(',', '')
                    title_abbrev = tab[1].strip()
                    case_corresp[title.lower()] = title
                    case_corresp[title_abbrev.lower()] = title_abbrev
                    journal2abbrev[title.lower()] = title_abbrev.lower()
                elif line != '': 
                    print('bib2reformat > Error in file ' + str(abbrev_dat.absolute) + ' at line ' + str(iline) + ', no XXX<>XXX separator: \n' + line)
    abbrev2journal = {ab: ti for ti, ab in journal2abbrev.items()}
    if abbrev == 0 : 
        journal_dat = abbrev2journal
    elif abbrev == 1 : 
        journal_dat = journal2abbrev
    titles_list = list(journal_dat.keys())
    titles_list.sort()
    target_list = [journal_dat[title] for title in titles_list]
    all_keys = list(case_corresp.keys())

    # Part 2 : parsing and correcting the bib
    missing_list = []
    missing_article = []
    inputbib = bib.split('\n')
    outputbib = ''
    iline = 0
    iarticle = 0
    for line in inputbib :
        iline += 1 
        clean = cleanline(line)
        if "@article"  in clean.replace(' ', '') : 
            article = clean.replace('@article{', '').replace(',', '')
        if "journal=" in clean.replace(' ', '') : 
            iarticle += 1
            stock_title = clean.split('=')[-1].replace(',', '').strip()[1:-1].strip()
            title = clean.split('=')[-1].replace(',', '').strip()[1:-1].replace('{', '').replace('}', '').strip()
            title = title.lower()
            found_title = False
            abbrev_title = title
            cleaner_title = title.replace('the', '').replace(',', '').strip()
            isintitles = title in titles_list or cleaner_title  in titles_list
            isintarget = title in target_list or cleaner_title in target_list
            if isintitles : 
                if title in titles_list : 
                    abbrev_title = journal_dat[title]
                elif cleaner_title  in titles_list : 
                    abbrev_title = journal_dat[cleaner_title]
            elif not isintarget : 
                missing_list.append(title)
                missing_article.append(article)

            if abbrev_title in all_keys : 
                abbrev_title = case_corresp[abbrev_title]
                line = line.replace(stock_title, abbrev_title)
        skip = False
        for key in exclusion_list : 
            if key.lower() + '=' in clean.replace(' ', '').lower():
                skip = True
        if not skip : 
            outputbib += '\n' + line
    for i, journal in enumerate(missing_list) : 
        print("bib2reformat > Article: " + missing_article[i] + '   ===>   missing abbreviation for journal:  ' + journal)
    return(outputbib, [missing_article, missing_list]) 

def bibfile2reformat(bibfile, abbrev, exclusion_list) : 
    """Given a .bib file and format rules returns a reformated .bib file."""
    from pathlib import Path
    if type(bibfile) == str : 
        pdf_file = Path(bibfile)
    outputfile = bibfile.with_suffix('.reformat.bib') 
    print("bibfile2reformat > Rewriting .bib file " + bibfile.name + " ==> into ==> " + outputfile.name) 
    bib = bibfile.open().read() 
    with outputfile.open(mode = 'w') as output:
        output.write(bib2reformat(bib, abbrev, exclusion_list)[0])

def savenonamebib(bib, dirpath) : 
    """Given a target directory and a bib string with no filename to save it into, tries the following filenames until one is not taken : 
    _ nameinbib.bib (nameinbib = the entry name in the bib, e.g. @article{author_year=nameinbib)
    _ JACS_nameinbib.bib (JACS is replaced by the initials of the journal name)
    _ JACS_nameinbib_2.bib
    _ JACS_nameinbib_3.bib
    ..."""
    from pathlib import Path
    openbib = bib.strip().split('\n')
    for line in openbib : 
        if line.strip().startswith('@') :
            name = line.split('{')[-1].replace(',', '').replace("'", '')
        elif line.strip().startswith('year') : 
            year = int(line.split('=')[-1].replace('{', '').replace('}', '').replace(',', '').strip())
        elif line.strip().startswith('journal') : 
            journame = line.split('=')[-1].replace('{', '').replace('}', '').lower().replace('the', '').replace('of', '').strip()
            while '  ' in journame : 
                journame = journame.replace('  ', ' ')
            journame = journame.split(' ')
            temp = ''
            if len(journame) == 1 : 
                temp = journame[0]
            else : 
                for word in journame : 
                    temp += word[0].upper()
            journame = temp
            filename = name + '.bib'
            if Path(filename).is_file() : 
                filename = journame + '_' + filename
                while Path(filename).is_file() : 
                    filename = filename.replace('.bib', '')
                    if filename.split('_')[-1].isdigit and int(filename.split('_')[-1]) != year: 
                        filename = filename[:-1] + str(int(filename[-1])+1) + '.bib'
                    else : 
                        filename = filename + '_2.bib'
    with Path(dirpath/filename).open(mode = 'w') as outputfile : 
        outputfile.write(bib) 
    return(filename)

def biburl(doi) : 
    """Given a doi returns the corresponding URL of api.crossref.org """
    return('http://api.crossref.org/works/' + doi + '/transform/application/x-bibtex')

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


