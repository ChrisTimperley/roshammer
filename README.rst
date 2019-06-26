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


Implementation
--------------

Classes
.......

* :code:`App` describes a ROS application provided by a given Docker image.
* :code:`AppInstance` provides an interface to an instance of a given
  :code:`App` that is running inside a Docker container.
* :code:`Input[T]` describes an input of type :code:`T` that can be produced by
  (non-destructively) applying a sequence of mutations to a seed object of
  type :code:`T`.

  * for the sake of efficiency, the concrete value for an input is computed
    lazily (and not cached) by accessing its :code:`value` property.
  * the :code:`mutate` method accepts a mutation (:code:`Mutation[T]`) as its
    sole parameter, and (non-destructively) produces a new input that adds the
    given mutation to the end of its sequence of mutations.

* :code:`InputInjector[T]`

* :code:`Mutation[T]` defines an interface for a callable object that accepts
  a single parameter of type :code:`T`, and (non-destructively) produces an
  output of type :code:`T` by applying the mutation described by the object.

  * :code:`DropMessage` is an example of a class that implements this interface
    for :code:`Bag` objects by returning a variant of an input bag with a
    single message removed, specified by the :code:`index` property of the
    :code:`DropMessage` object.

* :code:`Mutator[T]` defines an interface for a callable object that accepts
  an input of type :code:`Input[T]` and produces an output of the same type by
  generating and applying a mutation to that input. The mutator implements
  a strategy for mutating inputs.

* :code:`InputGenerator[T]` defines an interface for a class that generates a
  stream of fuzzing inputs (i.e., :code:`Input[T]`) according to a given
  strategy.

   * :code:`RandomInputGenerator` uses a given input mutator and a set of seed
     inputs to generate a random stream of single-order mutated inputs.

* :code:`Fuzzer[T]` uses a given input generator to fuzz a provided application.
