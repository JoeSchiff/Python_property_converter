from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize("/home/joepers/code/cpc/tests/input/trouble.pyx")
)
