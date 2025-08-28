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

def pdGb(x, by):
	if is_iterable(by):
		return x.groupby([k for k in x.index.names if k not in by])
	else:
		return x.groupby([k for k in x.index.names if k != by])

def pdSum(x,sumby):
	return pdGb(x, sumby).sum() if isinstance(x.index, pd.MultiIndex) else sum(x)
