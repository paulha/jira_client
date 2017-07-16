from distutils.core import setup

install_requires = {
    'argparse',
    'jira',
    'git+https://github.com/paulha/utility_funcs.git',
    'git+https://github.com/paulha/logger_yaml.git'
}

setup(
    name='jira_tools',
    version='0.1',
    packages=[''],
    package_dir={'': 'jira_tools'},
    url='',
    license='',
    author='paulhanchett',
    author_email='paul.hanchett@gmail.com',
    description=''
)
