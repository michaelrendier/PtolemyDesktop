#/usr/bin/python3
"""docstring for pydata"""

from dataclasses import dataclass

@dataclass
class Periodic():

	class H():
		name = 'Hydrogen'
		symbol = 'H'
		atomicnumber = 1
		category = 'nonmetal'
		group = 1
		period = 1
		block = 's'
		A_r = (1.00794, +7e-5, -7e-5) 
		electronconfig = '1s^1'
		electronpershell = 1
		oxidationstates = (1, -1, 'amphoteric oxide')
		electronegativity = (2.20, 'Pauling')
		ionizationenergy = (2.20, 'Pauling')
		covalentradius = (31, 'pm', +5, -5)
		vanderwallsradius = (120, 'pm')
		crystalstructure = 'hexagonal'
		magneticordering = 'diamagnetic'
		thermalconductivity = (0.1805, 'W/m*degK')
		speedofsound = (1310, 'm/s', 300.15, 'degK')
		casnumber = '1333-74-0'
		vaporpressure = {'p (Pa)': '@degK', 1: 'None', 1e1: 'None', 1e2: 'None', 1e3: 'None', 1e4: 15, 1e5: 20}
		color = 'None'
		phase = ('gas',289, 'degK')
		gdensity = (0.08988,'g/L', 0, 'degC', 101.325, 'kPa')
		sdensity = (0.763, 'g/cm^3')
		ldensitymp = (0.07,'g/cm^3')
		ldensitybp = (0.07099,'g/cm^3')
		meltingpoint = (14.01, 'degK')
		boilingpoint = (20.28, 'degK')
		triplepoint = (13.8033, 'degK', 7.042, 'kPa')
		criticalpoint = (32.97, 'degK', 1.293, 'MPa')
		fusionheat = (0.117, 'kJ/mol')
		vaporheat = (0.904, 'kJ/mol')
		molarheatcap = (28.863, 'J/mol*degK')
		
	class He():
		name = 'Helium'
		symbol = 'He'
		atomicnumber = 2
		category = 'Nobel Gases'
		group = 18
		period = 1
		block = 's'
		A_r = (4.002652, 2e-6)
		electronconfig = '1s2'
		electronpershell = 2
		oxidationstates = 'No Data'
		electronegativity = 'No Data'
		ionizationenergy = (2372.3, 'kj/mol', 5250.5, 'kJ/mol')
		covalentradius = (28, 'pm')
		vanderwallsradius = (135, 'pm')
		crystalstructure = 'hexagonal close packed'
		magneticordering = 'diamagnetic'
		thermalconductivity = (0.1513, 'W/m*K')
		speedofsound = (972, 'm/s')
		casnumber = '7435-59-7'
		vaporpressure = {'p (Pa)': '@degK', 1: 'None', 1e1: 'None', 1e2: 1.23, 1e3: 1.67, 1e4: 2.48, 1e5: 4.21}
		color = 'No data'
		phase = 'gas'
		gdensity = (0.1786, 'g/L', 0, 'degC', 101.325, 'kPa')
		sdensity = 'No Data'
		ldensitymp = (0.145, 'g/cm^3')
		ldensitybp = 'No Data'
		meltingpoint = (0.95, 'degK')
		boilingpoint = (4.22, 'degK')
		triplepoint = 'No Data'
		criticalpoint = (5.19, 'degK', 0.227, 'MPa')
		fusionheat = (0.0138, 'kJ/mol')
		vaporheat = (0.0829, 'kJ/mol')
		molarheatcap = (20.786, 'J/mol*degK')
		
	class Li():
		pass
	class Be():
		pass
	class B():
		pass
	class C():
		pass
	class N():
		pass
	class O():
		pass
	class F():
		pass
	class Ne():
		pass
	class Na():
		pass
	class Mg():
		pass
	class Al():
		pass
	class Si():
		pass
	class P():
		pass
	class S():
		pass
	class Cl():
		pass
	class Ar():
		pass
	class K():
		pass
	class Ca():
		pass
	class Sc():
		pass
	class Ti():
		pass
	class V():
		pass
	class Cr():
		pass
	class Mn():
		pass
	class Fe():
		pass
	class Co():
		pass
	class Ni():
		pass
	class Cu():
		pass
	class Zn():
		pass
	class Ga():
		pass
	class Ge():
		pass
	class As():
		pass
	class Se():
		pass
	class Br():
		pass
	class Kr():
		pass
	class Rb():
		pass
	class Sr():
		pass
	class Y():
		pass
	class Zr():
		pass
	class Nb():
		pass
	class Mo():
		pass
	class Tc():
		pass
	class Ru():
		pass
	class Rh():
		pass
	class Pd():
		pass
	class Ag():
		pass
	class Cd():
		pass
	class In():
		pass
	class Sn():
		pass
	class Sb():
		pass
	class Te():
		pass
	class I():
		pass
	class Xe():
		pass
	class Cs():
		pass
	class Ba():
		pass
	class La():
		pass
	class Hf():
		pass
	class Ta():
		pass
	class W():
		pass
	class Re():
		pass
	class Os():
		pass
	class Ir():
		pass
	class Pt():
		pass
	class Au():
		pass
	class Hg():
		pass
	class Tl():
		pass
	class Pb():
		pass
	class Bi():
		pass
	class Po():
		pass
	class At():
		pass
	class Rn():
		pass
	class Fr():
		pass
	class Ra():
		pass
	class Ac():
		pass
	class Rf():
		pass
	class Db():
		pass
	class Sg():
		pass
	class Bh():
		pass
	class Hs():
		pass
	class Mt():
		pass
	class Ds():
		pass
	class Rg():
		pass
	class Cn():
		pass
	class Uut():
		pass
	class Uuq():
		pass
	class Uup():
		pass
	class Uuh():
		pass
	class Uus():
		pass
	class Uuo():
		pass
	class Ce():
		pass
	class Pr():
		pass
	class Nd():
		pass
	class Pm():
		pass
	class Sm():
		pass
	class Eu():
		pass
	class Gd():
		pass
	class Tb():
		pass
	class Dy():
		pass
	class Ho():
		pass
	class Er():
		pass
	class Tm():
		pass
	class Yb():
		pass
	class Lu():
		pass
	class Th():
		pass
	class Pa():
		pass
	class U():
		pass
	class Np():
		pass
	class Pu():
		pass
	class Am():
		pass
	class Cm():
		pass
	class Bk():
		pass
	class Cf():
		pass
	class Es():
		pass
	class Fm():
		pass
	class Md():
		pass
	class No():
		pass
	class Lr():
		pass
class kitchenchem(object):
	pass
	
