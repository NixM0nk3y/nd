"""
This module contains the abstract base class Algorithm.
"""
from abc import ABC, abstractmethod
import inspect
from types import CodeType
from .utils import parallel


class Algorithm(ABC):

    @abstractmethod
    def apply(self, ds):
        return

    def parallel_apply(self, ds, dim, jobs=None):
        return parallel(self.apply, dim=dim, chunks=jobs)


def extract_arguments(fn, args, kwargs):
    """
    Given a function fn, return the leftover *args and **kwargs.
    """
    def _(*args, **kwargs):
        pass
    sig = inspect.signature(fn)
    if 'self' in sig.parameters:
        sig = sig.replace(parameters=tuple(sig.parameters.values())[1:])
    parameters = dict(sig.parameters)
    parameters.update(dict(inspect.signature(_).parameters))
    new_sig = sig.replace(parameters=tuple(parameters.values()))
    bound = new_sig.bind(*args, **kwargs)
    return bound.arguments


def wrap_algorithm(algo, name=None):
    """
    Return the function representation of an Algorithm derived class.

    NOTE: If algo.apply has *args and **kwargs parameters, this doesn't work.
    """
    if not issubclass(algo, Algorithm):
        raise ValueError('Class must be an instance of `nd.Algorithm`.')

    def _wrapper(*args, **kwargs):
        # First, apply the arguments to .apply():
        apply_kwargs = extract_arguments(algo.apply, args, kwargs)
        init_args = apply_kwargs.pop('args', ())
        init_kwargs = apply_kwargs.pop('kwargs', {})
        return algo(*init_args, **init_kwargs).apply(**apply_kwargs)

    # Override function module
    _wrapper.__module__ = algo.__module__

    # Override position of source code to fix source code links in
    # documentation. This is probably a bad idea.
    code = _wrapper.__code__
    new_filename = inspect.getfile(algo)
    caller = inspect.getframeinfo(inspect.stack()[1][0])
    new_firstlineno = caller.lineno
    new_code = CodeType(
        code.co_argcount,
        code.co_kwonlyargcount,
        code.co_nlocals,
        code.co_stacksize,
        code.co_flags,
        code.co_code,
        code.co_consts,
        code.co_names,
        code.co_varnames,
        new_filename,
        code.co_name,
        new_firstlineno,
        code.co_lnotab,
        code.co_freevars,
        code.co_cellvars
    )
    _wrapper.__code__ = new_code

    # Override function name
    if name is not None:
        _wrapper.__name__ = name

    # Override docstring
    link = ':class:`{}.{}`'.format(algo.__module__, algo.__name__)
    _wrapper.__doc__ = """Wrapper for {}.
    """.format(link) + algo.__doc__

    # Override signature
    sig_init = inspect.signature(algo.__init__)
    sig_apply = inspect.signature(algo.apply)
    parameters = tuple(sig_apply.parameters.values())[1:] + \
        tuple(sig_init.parameters.values())[1:]
    sig = sig_init.replace(parameters=parameters)
    _wrapper.__signature__ = sig

    return _wrapper