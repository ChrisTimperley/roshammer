roshammer
=========

.. image:: https://travis-ci.org/ChrisTimperley/roshammer.svg?branch=master
    :target: https://travis-ci.org/ChrisTimperley/roshammer

Installation
------------

To avoid interfering with the rest of your system (i.e., to avoid Python's
equivalent of DLL hell), we strongly recommend that
roshammer is installed within a
`virtualenv <https://virtualenv.pypa.io/en/latest/>`_ or
`pipenv <https://pipenv.readthedocs.io/en/latest/>`_ (pipenv is preferred).

From within the virtual environment (i.e., the `virtualenv` or `pipenv`),
roshammer can be installed from source:

.. code:: shell

   $ git clone git@github.com:ChrisTimperley/roshammer roshammer
   $ cd roshammer
   $ pipenv shell
   (roshammer) $ pip install .
