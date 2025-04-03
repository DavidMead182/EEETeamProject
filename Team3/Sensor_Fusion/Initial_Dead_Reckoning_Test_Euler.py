import numpy as np

#GITHUB LINK
#https://github.com/Mayitzin/ahrs/blob/master/ahrs/filters/aqua.py

#cd ./Documents/Fourth year/TDP4/Readings
#python3 Initial_Dead_Reckoning_Test.py

def integrate(x, dx, dt):
	return x + np.multiply(dx,dt)

def normalise(x):
	for i in range(len(x)):
		avg = np.sqrt((x[i,0]*x[i,0]) + (x[i,1]*x[i,1]) + (x[i,2]*x[i,2]))
		x[i,0] = x[i,0]/avg
		x[i,1] = x[i,1]/avg
		x[i,2] = x[i,2]/avg
	return x 

v = [0, 0, 0]
s = [0, 0, 0]

# =====================================
# File choice
# =====================================

fName = "Walking.txt"

timestep = 0.1013

alpha = 0.4
beta = 0.3

# =====================================
#Extraction of data from file
# =====================================

a_l = np.loadtxt(fName, delimiter = ',', usecols=(0, 1, 2))
g = np.loadtxt(fName, delimiter = ',', usecols=(3, 4, 5))
m = np.loadtxt(fName, delimiter = ',', usecols=(6, 7, 8))

a = normalise(a_l)
g = normalise(g)
m = normalise(m)

for i in range(1,len(a)):
	# =================================== #
	# Accelerometer
	# =================================== #
	if a[i][2] >= 0:
		q_acc = np.array([np.sqrt((a[i][0] + 1) / 2), -a[i][1]/np.sqrt(2*(a[i][2] + 1)), a[i][2]/np.sqrt(2*(a[i][2] + 1)), 0])

	else:
		q_acc = np.array([-a[i][1]/np.sqrt(2*(1 - a[i][2])), np.sqrt((1 - a[i][0]) / 2), 0, a[i][2]/np.sqrt(2*(a[i][2] + 1))])

	# =================================== #
	# Gyroscope
	# =================================== #
	cU = np.cos(g[i][0]/2)
	cV = np.cos(g[i][1]/2)
	cW = np.cos(g[i][2]/2)
	sU = np.sin(g[i][0]/2)
	sV = np.sin(g[i][1]/2)
	sW = np.sin(g[i][2]/2)

	q_gyr = np.array([cU*cV*cW + sU*sV*sW, sU*cV*cW - cU*sV*sW, cU*sV*cW + sU*cV*sW, cU*cV*sW - sU*sV*cW])

	# =================================== #
	# Magnetometer
	# =================================== #
	Gamma = m[i][0]*m[i][0] + m[i][1]*m[i][1]
	if m[i][0] >= 0:
		q_mag = np.array([np.sqrt(Gamma + m[i][0]*np.sqrt(Gamma))/np.sqrt(2*Gamma), 0, 0, m[i][1]/np.sqrt(2*(Gamma + m[i][0]*np.sqrt(Gamma)))])

	else:
		q_mag = np.array([m[i][1]/np.sqrt(2*(Gamma - m[i][0]*np.sqrt(Gamma))), 0, 0, np.sqrt(Gamma - m[i][0]*np.sqrt(Gamma))/np.sqrt(2*Gamma)])

	# =================================== #
	# Complimentary function
	# =================================== #
	for j in range(3):
		q_acc[j] *= alpha
		q_gyr[j] *= beta
		q_mag[j] *= (1-alpha-beta)
	q = q_acc + q_gyr + q_mag
	
# =================================================================== #
# ==================== Determining global angles ==================== #
# =================================================================== #

	roll = np.arctan( (2*(q[0]*q[1] + q[2]*q[3])) / (q[0]*q[0] - q[1]*q[1] - q[2]*q[2] + q[3]*q[3]) ) * 180/np.pi

	pitch = np.arcsin( (2*(q[0]*q[2] - q[1]*q[3])) ) * 180/np.pi

	yaw = np.arctan( (2*(q[0]*q[3] + q[1]*q[2])) / (q[0]*q[0] + q[1]*q[1] - q[2]*q[2] - q[3]*q[3]) ) * 180/np.pi	

	#print(f"Roll: {roll:.3f}    pitch: {pitch:.3f}    heading: {yaw:.3f}")
	
# =================================================================== #
# ================ Determining transformation matrix ================ #
# =================================================================== #

	R_x = [[1, 0, 0],[0, np.cos(pitch), -np.sin(pitch)], [-np.sin(pitch), 0, np.cos(pitch)]]

	R_y = [[np.cos(roll), 0, np.sin(roll)], [0, 1, 0], [-np.sin(roll), 0, np.cos(roll)]]

	R_z = [[np.cos(yaw), -np.sin(yaw), 0], [np.sin(yaw), np.cos(yaw), 0],[0, 0, 1]]

# =================================================================== #
# ================= Determining global acceleration ================= #
# =================================================================== #

	R = np.matmul(np.matmul(R_x, R_y), R_z)
	a_g = np.matmul(R, np.transpose(a_l[i]))
	a_g[2] -= 9.81

	v = integrate(v, a_g, timestep)
	s = integrate(s, v, timestep)

	print(f"Global:  x = {s[0]:.3f}  y = {s[1]:.3f}  z = {s[2]:.3f}")



