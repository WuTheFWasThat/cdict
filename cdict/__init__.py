from .main import cdict_base as C

cdict = C.dict
cfinaldict = C.finaldict
cdefaultdict = C.defaultdict
citer = C.iter
clist = C.list
csum = C.sum

__all__ = ['C', 'cdict', 'cfinaldict', 'cdefaultdict', 'citer', 'clist', 'csum']
