#! /usr/bin/env python3

import os, re, shutil, glob
from setuptools import setup, find_packages, Command

class CleanCommand(Command):
    """Custom clean command to tidy up the project root."""

    CLEAN_FILES = ('./build', './dist', './*.pyc', './*.tgz', './*.egg-info')
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        root = os.path.dirname(__file__)
        for path in self.CLEAN_FILES:
            path = os.path.normpath(os.path.join(root, path))
            for path in glob.glob(path):
                print('removing {}'.format(os.path.relpath(path)))
                shutil.rmtree(path, ignore_errors=True)

def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()

def read_reqs(fname):
    with open(fname, 'r') as f:
        lines = f.read().split('\n')
        lines = [re.sub(r'[\s]*(#.*)?$', '', x) for x in lines]
        lines = [x for x in lines if x]
    return lines

setup(
    name = 'vkts',
    fullname = 'VK Thematic Search',
    version = '0.0.1',
    author = 'Denis Stepnov',
    author_email = 'stepnovdenis@gmail.com',
    url = 'https://github.com/smurphik/vkts',
    description = ('Library of accelerated access to vk API'
                   ' & thematic students search tool'),
    long_description = read('README.md'),
    long_description_content_type = 'text/markdown',
    license = 'MIT',
    keywords = 'vk social network web scraping',
    packages = find_packages(exclude=['tests']),
    install_requires = read_reqs('requirements.txt'),
    cmdclass = {'clean': CleanCommand},
    entry_points = {'console_scripts': ['vkts = vkts.__main__:main']},
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Topic :: Internet :: WWW/HTTP',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
    ],
)

