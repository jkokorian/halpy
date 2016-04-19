from setuptools import setup

setup(name='halpy',
      version='0.1',
      description='Hardware Abstraction Layer (HAL) code generation framework for python.',
      url='http://github.com/jkokorian/halpy',
      author='J. Kokorian',
      author_email='J.Kokorian@TUDelft.nl',
      license='none',
      packages=[
          'halpy',
          ],
      entry_points='''
        [console_scripts]
        odms=halpy.commandline:cli
    ''',
      install_requires=['Click','pyyaml'],
      zip_safe=False)