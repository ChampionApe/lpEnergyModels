import itertools, numpy as np, pandas as pd
from collections.abc import Iterable
from six import string_types
from pyDbs import adj, adjMultiIndex, ExcelSymbolLoader, Broadcast, Gpy, Gpy_, GpySet, GpyVariable, GpyScalar, GpyDict, SimpleDB
from pyDbs import cartesianProductIndex as CPI
from symMaps import Lag, Lead, Roll, AMatrix, AMDict, LPSys, ModelShell, loopUnpackToDFs
import symMaps

def noneInit(x,FallBackVal):
	return FallBackVal if x is None else x

def is_iterable(arg):
	return isinstance(arg, Iterable) and not isinstance(arg, string_types)

def getIndex(symbol):
	""" Defaults to None if no index is defined. """
	if hasattr(symbol, 'index'):
		return symbol.index
	elif isinstance(symbol, pd.Index):
		return symbol
	elif not is_iterable(symbol):
		return None

def reorder(v, order=None):
	return v.reorder_levels(noneInit(order, sorted(getIndex(v).names))) if isinstance(getIndex(v), pd.MultiIndex) else v

def pdGb(x, by):
	if not is_iterable(by):
		by = [by]
	gb = [k for k in x.index.names if k not in by]
	return x.groupby(gb) if gb else x

def pdSum(x,sumby):
	return pdGb(x, sumby).sum() if isinstance(x.index, pd.MultiIndex) else sum(x)
