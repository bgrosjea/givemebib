#!/usr/bin/env/ python
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



