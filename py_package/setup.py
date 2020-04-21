import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="givemebib",
    version="1.0.1",
    author="Benoit Grosjean",
    author_email="grosjean.benoit@gmail.com",
    description="Provides clean .bib files, with possible abbreviation of journal titles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bgrosjea/givemebib",
    include_package_data=True, 
    package_dir={'givemebib': 'givemebib/'},
    package_data={'givemebib': ['journal_abbreviations.dat', 'givemebib.ini']},
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5.6',
    install_requires=requirements,
    entry_points={"console_scripts": ["givemebib=givemebib.__main__:main"]}
)
