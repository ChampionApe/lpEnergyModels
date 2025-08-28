from lpEnergyModels.base import *
_adjF = adj.rc_pd

# A few basic functions for the energy models:
def fuelCost(pFuel, uEm, taxEm):
	""" 
	 - 'pFuel' (fuel price) is defined over 'idxF' (fuel index). Default unit: €/GJ.
	 - 'uEm' (emission intensity) is defined over 'idxF','idxEm' (emission index). Default unit: Ton emission/GJ fuel input. 
	 - 'taxEm' (tax on emissions) is defined over 'idxEm' (emission index). Default unit: €/ton emission output.
	"""
	return pFuel.add(pdSum((uEm * taxEm).dropna(), 'idxEm'), fill_value=0)

def mc(uFuel, VOM, pFuel, uEm, taxEm):
	""" 
	- 'uFuel': Fuelmix is defined over 'idxF', 'idxGen' (generator index). Default unit: GJ input/GJ output.
	- 'VOM': variable operating and maintenance costs is defined over 'idxGen'. Default unit: €/GJ output.
	"""
	return pdSum((uFuel * fuelCost(pFuel, uEm, taxEm)).dropna(), 'idxF').add(VOM, fill_value=0)

def fuelConsumption(generation, uFuel, sumOver='idxGen'):
	"""
	- 'generation': dispatched energy defined over 'idxGen'. Default unit: GJ.
	- 'uFuel': Fuelmix is defined over 'idxF', 'idxGen' (generator index). Default unit: GJ input/GJ output.
	"""
	return pdSum((generation * uFuel).dropna(), sumOver)

def emissionsFuel(fuelCons, uEm, sumOver='idxF'):
	""" 
	- 'fuelCons': fuel input defined over 'idxF'. Default unit: GJ. 
	 - 'uEm' (emission intensity) is defined over 'idxF','idxEm' (emission index). Default unit: Ton emission/GJ fuel input. 
	"""
	return pdSum((fuelCons * uEm).dropna(), sumOver)

def plantEmissionIntensity(uFuel, uEm):
	""" 
	- 'uFuel': Fuelmix is defined over 'idxF', 'idxGen' (generator index). Default unit: GJ input/GJ output.
	 - 'uEm' (emission intensity) is defined over 'idxF','idxEm' (emission index). Default unit: Ton emission/GJ fuel input. 
	"""
	return (uFuel * uEm).groupby('idxGen').sum()

class MBasic(ModelShell):
	def compile(self, computeMC = True, **kwargs):
		""" Compile model """
		if computeMC:
			self.updateMC()
		self.initArgs()
		return self.sys.compile(**kwargs)

	def updateMC(self):
		self.db['mc'] = mc(self.db('uFuel'), self.db('VOM'), self.db('pFuel'), self.db('uEm'), self.db('taxEm'))

	def initArgs(self):
		[getattr(self, f'initArgs_{k}')() for k in ('v','eq','ub') if hasattr(self, f'initArgs_{k}')]; # specify domains for variables and equations
		[getattr(self, f'initArgsV_{k}')() for k in self.sys.v]; # specify c,l,u for all variables
		[getattr(self, f'initArgsEq_{k}')() for k in self.sys.eq]; # add A_eq and b_eq.
		[getattr(self, f'initArgsUb_{k}')() for k in self.sys.ub]; # add A_ub and b_ub.

	def initArgs_v(self):
		""" self.sys.v dictionary"""
		self.sys.v.update({'generation': self.db('idxGen'),'demand': self.db('idxCons')})

	def initArgs_eq(self):
		""" self.sys.eq dictionary"""
		self.sys.eq.update({'equilibrium': None})

	def initArgsV_generation(self):
		self.sys.lp['c'][('mc', 'generation')] = self.db('mc') # assumes that mc is defined over index 'idxGen'.
		self.sys.lp['u'][('genCap', 'generation')] = self.db('genCap') # assumes that genCap is defined over index 'idxGen'.

	def initArgsV_demand(self):
		self.sys.lp['c'][('mwp', 'demand')] = -self.db('mwp') # assumes that mwp is defined over index 'idxCons'.
		self.sys.lp['u'][('loadCap', 'demand')] = self.db('load') # assumes that load is defined over index 'idxCons'.

	def initArgsEq_equilibrium(self):
		self.sys.lazyA('eq2Gen', series = 1,  v = 'generation', constr = 'equilibrium',attr='eq')
		self.sys.lazyA('eq2Dem', series = -1, v = 'demand', constr = 'equilibrium',attr='eq')

	def postSolve(self, sol, **kwargs):
		solDict = super().postSolve(sol)
		solDict['surplus'] = -sol['fun']
		solDict['fuelCons'] = fuelConsumption(solDict['generation'], self.db('uFuel'))
		solDict['emissions'] = emissionsFuel(solDict['fuelCons'], self.db('uEm'))
		return solDict

class MBasicEmCap(MBasic):
	# Add additional constraint:
	def initArgs_ub(self):
		""" self.sys.ub dictionary"""
		self.sys.ub.update({'emCap': None})

	def initArgsUb_emCap(self):
		self.sys.lazyA('emCap2Gen', series = plantEmissionIntensity(self.db),  v = 'generation', constr = 'emCap',attr='ub')
		self.sys.lp['b_ub'] = self.db('CO2Cap')


class MBasicRES(MBasic):

	def RESGenIdx(self, CO2Idx = 'CO2'):
		""" Subset of idxGen that is considered Renewable Energy based on emission intensities """
		s = self.db('uFuel') * self.db('uEm').xs(CO2Idx,level='idxEm')
		return s[s <= 0].index

	def initArgs_ub(self):
		""" self.sys.ub dictionary"""
		self.sys.ub.update({'RES': None})

	def initArgsUb_emCap(self):
		self.sys.lazyA('RES2Gen', series = pd.Series(-1, index = self.RESGenIdx()),  v = 'generation', constr = 'RES',attr='ub')
		self.sys.lazyA('RES2Dem', series = pd.Series(self.db('RESCap'), index = self.RESGenIdx()),  v = 'generation', constr = 'RES',attr='ub')
