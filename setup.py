from setuptools import setup, find_packages
setup(name="pyec", 
	package_dir={'':'src'},
	version="0.1",
	packages=find_packages('src'),
	scripts=['src/pyecd'])
