#!/usr/bin/python
import os

virtenv = os.path.join(os.environ.get('OPENSHIFT_PYTHON_DIR','.'), 'virtenv')
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    execfile(virtualenv, dict(__file__=virtualenv))
    exec_namespace = dict(__file__=virtualenv)
    with open(virtualenv, 'rb') as exec_file:
        file_contents = exec_file.read()
    compiled_code = compile(file_contents, virtualenv, 'exec')
    exec(compiled_code, exec_namespace)

except IOError:
    pass
#
# IMPORTANT: Put any additional includes below this line.  If placed above this
# line, it's possible required libraries won't be in your searchable path
#

from sports import app as application
