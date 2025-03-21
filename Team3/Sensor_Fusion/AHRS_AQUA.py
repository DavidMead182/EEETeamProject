import numpy as np
import ahrs.filters as filters

#GITHUB LINK
#https://github.com/Mayitzin/ahrs/blob/master/ahrs/filters/aqua.py

#cd ./Documents/Fourth year/TDP4/Readings
#python3 AHRS_AQUA.py

# =====================================
# File choice
# =====================================

fName = "Walking.txt"


# =====================================
#Extraction of data from file
# =====================================

a = np.loadtxt(fName, delimiter = ',', usecols=(0, 1, 2))
g = np.loadtxt(fName, delimiter = ',', usecols=(3, 4, 5))
m = np.loadtxt(fName, delimiter = ',', usecols=(6, 7, 8))

print(np.shape(a))

# =====================================
# Filter implementation
# =====================================

AquaFilter = filters.aqua.AQUA(frequency = 10.1, adaptive = True)


q = AquaFilter.estimate(a[0], m[0])
#Value to which the method stops using spherical and just uses linear
threshold = 0.3 
Gain = 0.1

for i in range(1,len(a)):
	#q gives the quaternion output from the IMU
	q = AquaFilter.updateMARG(q, gyr = g[i], acc = a[i], mag = m[i])

	#Estimates the gain 'alpha'
	Gain = filters.aqua.adaptive_gain(a_local = a[i], gain = Gain)

	#Interpolation with identity quaternion
	q_int = filters.aqua.slerp_I(q, Gain, threshold)
	Omega = AquaFilter.Omega(g[i]) 
	print(q)
	

