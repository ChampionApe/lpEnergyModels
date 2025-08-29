from lpEnergyModels.base import *
_adjF = adj.rc_pd

def mc(uFuel, VOM, pFuel, uEm, taxEm):
	"""See mBasic"""
	return pdSum((uFuel * fuelCost(pFuel, uEm, taxEm)).dropna(), 'idxF').add(VOM, fill_value=0)

def fuelCost(pFuel, uEm, taxEm):
	"""See mBasic"""
	return pFuel.add(pdSum((uEm * taxEm).dropna(), 'idxEm'), fill_value=0)

def plantEmissionIntensity(uFuel, uEm):
	"""See mBasic"""
	return (uFuel * uEm).groupby(['idxGen','idxEm']).sum()

def mcHr(uFuel, VOM, pFuel, uEm, taxEm, idxHr):
	return Broadcast.seriesToIdx(mc(uFuel, VOM, pFuel, uEm, taxEm), idxHr)

def fuelConsumption(generation, uFuel, scale, sumOver = ['idxGen','idxH']):
	""" Yearly fuel consumption in GJ across 'idxF'. scale maps to yearly levels. For instance, a model featuring 24 hours uses scale = 8760/24. """
	return scale * pdSum((generation * uFuel).dropna(), sumOver)

def emissionsFuel(fuelCons, uEm, sumOver='idxF'):
	""" See mBasic"""
	return pdSum((fuelCons * uEm).dropna(), sumOver)

def unitGenSRC(mcHr, generation, genCap, scale):
	""" Yearly short run costs per unit of installed generating capacity. Unit: (1000€ /(GJ/hour generating capacity) / year)"""
	return (pdSum(mcHr * generation, 'idxHr') * scale)/(1000 * genCap)

def unitGenLRC(FOM, INVC):
	""" Yearly, annualized costs in 1000€ / (GJ/hour generating capacity)"""
	return (FOM.add(INVC, fill_value=0))

def unitGenC(mcHr, FOM, INVC, generation, genCap, scale):
	""" Yearly, annualized costs in 1000€ / (GJ/hours generating capacity)"""
	return unitGenSRC(mcHr, generation, genCap, scale).add(unitGenLRC(FOM, INVC), fill_value=0)

def utilGenCap(generation, genCap, idxHr):
	""" Theoretical capacity factor ∈ [0,1]. """
	return pdSum(generation,'idxHr')/(len(idxHr) * genCap)

def utilGenCapHVT(generation, genCapHr):
	""" 'Practical' capacity factor ∈[0,1]. ≥ theoretical cap. factor. """
	return pdSum(generation, 'idxHr')/pdSum(genCapHr, 'idxHr')

def avgGenPrice(generation, pHr, sumOver = 'idxHr'):
	""" Average price €/GJ received for different generators """
	return pdSum(pHr * generation, sumOver) / pdSum(generation, sumOver)

def mEV(λGeneration, uHrGenCap, FOM, INVC, genCap, scale):
	""" Marginal economic value from marginal increase in capacity by 1 GJ/hour, defined over 'idxGen'. Default unit: 1000€/(GJ/hour generating capacity)"""
	return (scale * pdSum(- λGeneration * uHrGenCap, 'idxHr')/1000 ).sub(unitGenLRC(FOM, INVC), fill_value=0)


class MBasicInt(ModelShell):
	def compile(self, updateAux = True, keys = None, **kwargs):
		""" Compile model """
		self.compileMaps()
		if updateAux:
			self.updateAux(keys = None)
		return self.compileParams()

	@property
	def scale(self):
		return 8760/len(self.db('idxHr'))

	def updateAux(self, keys = None):
		[self.db.__setitem__(k, getattr(self, f'aux_{k}')) for k in noneInit(keys, ['mcHr', 'genCapHr','loadHr'])]; # update auxiliary variables

	@property
	def aux_mcHr(self):
		return reorder(mcHr(self.db('uFuel'), self.db('VOM'), self.db('pFuel'), self.db('uEm'), self.db('taxEm'), self.db('idxHr')), order = self.sys.v['generation'].names)

	@property
	def aux_genCapHr(self):
		return reorder(self.aux_uHrGenCap * self.db('genCap'), order = self.sys.v['generation'].names)

	@property
	def aux_uHrGenCap(self):
		return Broadcast.seriesToIdx(self.db('uHrCap'), self.db('idxGen2HVTGen')).droplevel('idxHVTGen')

	@property
	def aux_loadHr(self):
		return reorder(Broadcast.seriesToIdx(self.db('uHrLoad'), self.db('idxCons2HVTCons')).droplevel('idxHVTCons') * self.db('load'), order = self.sys.v['demand'].names)

	def compileMaps(self):
		[getattr(self, f'initArgs_{k}')() for k in ('v','eq','ub') if hasattr(self, f'initArgs_{k}')]; # specify domains for variables and equations
		self.sys.compileMaps()

	def initArgs_v(self):
		""" self.sys.v dictionary"""
		self.sys.v.update({'generation': pd.MultiIndex.from_product([self.db('idxHr'), self.db('idxGen')]),
							'demand': pd.MultiIndex.from_product([self.db('idxHr'), self.db('idxCons')])})

	def initArgs_eq(self):
		""" self.sys.eq dictionary"""
		self.sys.eq.update({'equilibrium': self.db('idxHr')})

	def compileParams(self):
		[getattr(self, f'initArgsV_{k}')() for k in self.sys.v]; # specify c,l,u for all variables
		[getattr(self, f'initArgsEq_{k}')() for k in self.sys.eq]; # add A_eq and b_eq.
		[getattr(self, f'initArgsUb_{k}')() for k in self.sys.ub]; # add A_ub and b_ub.
		self.sys.compileParams()
		return self.sys.out

	def initArgsV_generation(self):
		self.sys.lp['c'][('mc', 'generation')] = self.db('mcHr') # assumes that mc is defined over index 'idxGen'.
		self.sys.lp['u'][('genCap', 'generation')] = self.db('genCapHr') # assumes that genCap is defined over index 'idxGen'.

	def initArgsV_demand(self):
		self.sys.lp['c'][('mwp', 'demand')] = reorder(-Broadcast.seriesToIdx(self.db('mwp'), self.sys.v['demand']), order = self.sys.v['demand'].names)
		self.sys.lp['u'][('loadCap', 'demand')] = self.db('loadHr')

	def initArgsEq_equilibrium(self):
		self.sys.lazyA('eq2Gen', series = 1,  v = 'generation', constr = 'equilibrium',attr='eq')
		self.sys.lazyA('eq2Dem', series = -1, v = 'demand', constr = 'equilibrium',attr='eq')

	def postSolve(self, sol, **kwargs):
		solDict = super().postSolve(sol)
		solDict['surplus'] = -sol['fun']
		solDict['fuelCons'] = fuelConsumption(solDict['generation'], self.db('uFuel'), self.scale)
		solDict['emissions'] = emissionsFuel(solDict['fuelCons'], self.db('uEm'))
		solDict['utilGenCap'] = utilGenCap(solDict['generation'], self.db('genCap'), self.db('idxHr'))
		solDict['utilGenCapHVT'] = utilGenCapHVT(solDict['generation'], self.db('genCapHr'))
		solDict['unitGenCapCosts'] = unitGenC(self.db('mcHr'), self.db('FOM'), self.db('INVC'), solDict['generation'], self.db('genCap'), self.scale)
		solDict['pHr'] = solDict['λeq_equilibrium'] # marginal prices = marginal system costs
		solDict['pAvg'] = avgGenPrice(solDict['generation'], solDict['pHr'], sumOver = ['idxHr','idxGen'])
		solDict['pAvgGen'] = avgGenPrice(solDict['generation'], solDict['pHr'], sumOver = 'idxHr')
		solDict['downlift'] = solDict['pAvg']-solDict['pAvgGen']
		solDict['mEV'] = mEV(solDict['λu_generation'], self.aux_uHrGenCap, self.db('FOM'), self.db('INVC'), self.db('genCap'), self.scale)
		return solDict


class MBasicIntEmCap(MBasicInt):
	# Add additional constraint:
	def initArgs_ub(self):
		""" self.sys.ub dictionary"""
		self.sys.ub.update({'emCap': self.db('idxEm')})

	def initArgsUb_emCap(self):
		self.sys.lazyA('emCap2Gen', series = plantEmissionIntensity(self.db('uFuel'),self.db('uEm')),  v = 'generation', constr = 'emCap',attr='ub')
		self.sys.lp['b_ub'][('emCap','emCap')] = self.db('emCap')

class MBasicIntRES(MBasicInt):

	def RESGenIdx(self, CO2Idx = 'CO2'):
		""" Subset of idxGen that is considered Renewable Energy based on emission intensities """
		s = (self.db('uFuel') * self.db('uEm').xs(CO2Idx,level='idxEm')).groupby('idxGen').sum()
		return s[s <= 0].index

	def initArgs_ub(self):
		""" self.sys.ub dictionary"""
		self.sys.ub.update({'RES': None}) # scalar constraint

	def initArgsUb_RES(self):
		""" Specify vIdx for 'generation' to indicate that only a subset of the index for 'generation' should enter with -1. """
		self.sys.lazyA('RES2Gen', series = -1,  v = 'generation', constr = 'RES', vIdx = reorder(Broadcast.idx(self.RESGenIdx(), self.sys.v['generation']), self.sys.v['generation'].names), attr='ub')
		self.sys.lazyA('RES2Dem', series = self.db('RESCap'), v = 'demand', constr = 'RES',attr='ub')
