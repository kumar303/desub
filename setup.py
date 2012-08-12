import os

from setuptools import setup, find_packages


def path(name):
    return open(os.path.join(os.path.dirname(__file__), name))


setup(name='desub',
      version='1.0',
      description='Work with a detached subprocess.',
      long_description=path('README.rst').read(),
      author='Kumar McMillan',
      author_email='kumar.mcmillan@gmail.com',
      license='MIT',
      url='https://github.com/kumar303/desub',
      include_package_data=True,
      classifiers=[],
      packages=find_packages(exclude=['tests']),
      install_requires=[ln.strip() for ln in
                        path('requirements.txt')
                        if not ln.startswith('#')])
