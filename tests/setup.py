from setuptools import setup
from Cython.Build import cythonize
from pathlib import Path


base_path = Path(__file__).parent

setup(ext_modules=cythonize(f"{base_path}/input/trouble.pyx"))
