from setuptools import setup

setup(
    name='pdfParser',
    version='0.1',
    packages=[''],
    url='https://github.com/kiem-group/pdfParser',
    license='MIT',
    author='Natallia Kokash',
    author_email='natallia.kokash@gmail.com',
    description='Experimental pipeline to create knowledge graphs from Arts and Humanities publications',
    python_requires='>=3.0.*',
    install_requires=['zipfile', 'logging', 'lxml', 'pdfminer', 'Levenshtein', 'csv', 'bibtexparser', 'pyparsing',
                      'dataclasses', 'dataclasses-json', 'pdoc3', 'neo4j', 'json', 'abc', 'importlib_resources',
                      'surf@ git+https://github.com/franzlst/surfrdf@master#egg=surf',
                      'hucitlib@ git+https://github.com/mromanello/hucitlib.git'
                      ],
    test_suite='test'
)
