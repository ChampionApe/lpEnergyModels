from lpEnergyModels.base import *
_adjF = adj.rc_pd

class MBasicPH(ModelShell):
	def compile(self, updateAux = True, keys = None, **kwargs):
		""" Compile model """
		self.compileMaps()
		if updateAux:
			self.updateAux(keys = None)
		return self.compileParams()

	def compileMaps(self):
		[getattr(self, f'initArgs_{k}')() for k in ('v','eq','ub') if hasattr(self, f'initArgs_{k}')]; # specify domains for variables and equations
		self.sys.compileMaps()

	def compileParams(self):
		[getattr(self, f'initArgsV_{k}')() for k in self.sys.v]; # specify c,l,u for all variables
		[getattr(self, f'initArgsEq_{k}')() for k in self.sys.eq]; # add A_eq and b_eq.
		[getattr(self, f'initArgsUb_{k}')() for k in self.sys.ub]; # add A_ub and b_ub.
		self.sys.compileParams()
		return self.sys.out
