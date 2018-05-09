from distutils.core import setup

install_requires = {
    'jira',
    'git+https://github.com/paulha/utility_funcs.git',
    'pytest',
    'PyYAML'
}

setup(
    name='jira_client',
    version='0.1',
    packages=['jira_client'],
    # package_dir={'': 'jira_tools'},
    url='',
    license='',
    author='Paul Hanchett',
    author_email='paul.hanchett@gmail.com',
    description=''
)
