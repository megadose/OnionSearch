# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(
    name='onionsearch',
    version="1",
    packages=find_packages(),
    author="megadose",
    install_requires=["requests","argparse","termcolor","tqdm", "html5lib","bs4"],
    description="OnionSearch is a script that scrapes urls on different .onion search engines.",
    include_package_data=True,
    url='http://github.com/megadose/OnionSearch',
    entry_points = {'console_scripts': ['onionsearch = onionsearch.core:scrape']},
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
