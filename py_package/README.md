# *givemebib*
*givemebib* is a bibliographic tool for scientific litterature that does two things: 

1) provides **clean .bib files** downloaded from <http://api.crossref.org/works/>

2) reformats .bib files by outputing **abbreviated or full journal names** and by **deleting specified information fields** (e.g. url, doi, abstract...)

It can do so starting from several **input** types: 

* .pdf file of article 
* directory with .pdf files of articles
* doi of article (e.g. '10.1234/123blabla-(bla).7810')
* list of doi written in a file and separated by tabulations, new lines and white spaces (see [this sample](https://github.com/bgrosjea/givemebib/blob/master/samples/doi_list))
* Google Scholar query (e.g. 'author:Smith 2020 graphene ~device -nanotube')
* list of Google Scholar queries written in a file on separate lines (see [this sample](https://github.com/bgrosjea/givemebib/blob/master/samples/query_list))
* .bib file to be formated

It does not work 100% of the time for .pdf files and Google Scholar queries. 

The sample files in the [samples](https://github.com/bgrosjea/givemebib/blob/master/samples/) directory are meant to also show some of the error messages, hence some input files would not yield all the bib information. 

## How to install: 

### Using pip

Run in terminal: 
`pip install givemebib`

### Manually

1) Download the [compressed directory](https://github.com/bgrosjea/blob/master/givemebib_py.zip/).
2) In the extracted downloaded directory, run in terminal: `python setup.py install` or `python3 setup.py install`

## How to run it:  
### with Command line

Run in terminal: 

`givemebib <target> <0 or 1>`

* target is one of the input types described above
* 0 will transform output .bib files to include full journal names
* 1 will transform output .bib files to include abbreviated journal names

If the *givemebib* command is unknown, make sure python packages are added to your PATH system variable. 


### single functions in python script

Single functions used in the main script can be run in a python script : 
```python
import givemebib.functions as gmb
pdf = './example.pdf'
doi = gmb.pdf2doi(pdf)
...
```

Functions: 

* **scholarquery2doi(query)** given a search query (string), returns the doi of the first Google Scholar result. 
* **pdfminer2doi(pdf)** given the path to a .pdf file (string), tries to finds the doi in the .pdf using pdfminer.six and tries the figure captions as Google Scholar queries if not until a doi is found on the first search result link. This function is integrated in pdf2doi, which should be preferred. 
* **pdf2doi(pdf)** given the path to a .pdf file (string), tries to finds the doi in the .pdf first using PyPDF2, then pdfminer2doi
* **doi2bib(doi)** given a doi (string starting with '10.'), returns bib as a string, as downloaded from <http://api.crossref.org/works/>
* **pdf2bib(pdf)** given the path to a .pdf file (string), returns bib as a string. Interfaces pdf2doi and doi2bib. 
* **pdf2bibfile(pdf)** given the path to a .pdf file (string), saves bib in file pdfname.bib
* **bib2reformat(bib, abbrev, exclusion_list)** given a bib (string), 0 (non abbreviated journal names in output) or 1 (abbreviated journal names in output), a list of information fields to delete (e.g. ['url', 'doi', 'month',...]), returns a reformated bib string without the fields listed and with abbreviated (abbrev=1) or not (abbrev=0) journal names.
* **bibfile2reformat(bib, abbrev, exclusion_list)** given a .bib file, abbrev (0 or 1) and exclusion_list (see above), writes a reformated bib file as bibname.reformat.bib
* **savenonamebib(bib, directory)** given a bib string and the path to a directory, saves the bib in a .bib file in the directory, naming it after information from the bib. It tries several names until one is not an existing file: nameinbib.bib, journalInitials_nameinbib.bib, journalInitials_nameinbib_2.bib, ...
* **biburl(doi)** given a doi (string) returns the corresponding bib url on crossref.org: http://api.crossref.org/works/doi/transform/application/x-bibtex

### Necessary files

Those two files should be automatically installed
* information fields to delete are to be entered in file *givemebib.ini* 
* journal names and their abbreviations are stored in *journal_abbreviations.dat*, additional entries can be written with 'XXX<>XXX' as separator. Most abbreviations were found on <http://guides.lib.berkeley.edu/bioscience-journal-abbreviations/>

    Additional abbreviations can be found for instance on wikipedia or on:

    * <http://cassi.cas.org/search.jsp>

    * <http://www.journalabbr.com/>

    * <https://journal-abbreviations.library.ubc.ca/>

### Error output

In the directory of execution, the file *givemebib.log* stores errors encountered such as: 

* inputs that gave no results (.pdf files from which no *doi* was extracted, incorrect *doi* etc.)

* inputs that gave possibly wrong results (.pdf from which the *doi* extracted had to be modified to yield a result or required a Google Scholar search)

* journal names or abbreviations not detected or stored in *journal_abbreviations*.dat

## How it works

To obtain a .bib, the *doi* of the article is read either as provided, extracted from a .pdf or from the webpage of the first Google Scholar result of a provided search query. The .bib is then downloaded using this url: <http://api.crossref.org/works/theDOI/transform/application/x-bibtex>

The extraction of a *doi* from an article does not always work right. Sometimes no *doi* is found, sometimes a *doi* with extra characters is found. In that latter case, the last characters of the *doi* are progressively removed until a match is found on crossref.org. To limit errors, three methods are used in the following order: i) with the pdf read by PyPDF2; ii) with the pdf read by pdfminer.six; iii) by using figure captions of the article as Google Scholar queries until a doi is found on the webpage of the first search result. The last method does not work well as: i) figure captions as queries do not always give a result nor the right one; ii) the IP address can get blocked by Google Scholar after multiple queries; iii) sometimes the doi of another article is detected on the page. This might be subject to future improvements. 

All bib are then reformatted before being written into files. 

## License

GNU General Public License v3 (GPLv3)

## Credit

Benoit Grosjean : <https://github.com/bgrosjea>
