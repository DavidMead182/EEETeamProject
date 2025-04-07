import numpy as np

#GITHUB LINK
#https://github.com/Mayitzin/ahrs/blob/master/ahrs/filters/aqua.py

#cd ./Documents/Fourth year/TDP4/Readings
#python3 Initial_Dead_Reckoning_Test.py

def integrate(x, dx, dt):
	return x + np.multiply(dx,dt)

v = [0, 0, 0]
s = [0, 0, 0]

# =====================================
# File choice
# =====================================

fName = "Walking.txt"

alpha = 0.2 #Accelerometer
beta = 0.5  #Gyroscope

timestep = 0.1013


# =====================================
#Extraction of data from file
# =====================================

a = np.loadtxt(fName, delimiter = ',', usecols=(0, 1, 2))
g = np.loadtxt(fName, delimiter = ',', usecols=(3, 4, 5))
m = np.loadtxt(fName, delimiter = ',', usecols=(6, 7, 8))

# =====================================
# Filter implementation
# =====================================

for i in range(len(a)):
	# =================================== #
	# Accelerometer
	# =================================== #
	if a[i][2] >= 0:
		q_acc = [np.sqrt((a[i][0] + 1) / 2), -a[i][1]/np.sqrt(2*(a[i][2] + 1)), a[i][2]/np.sqrt(2*(a[i][2] + 1)), 0]

	else:
		q_acc = [-a[i][1]/np.sqrt(2*(1 - a[i][2])), np.sqrt((1 - a[i][0]) / 2), 0, a[i][2]/np.sqrt(2*(a[i][2] + 1))]

	# =================================== #
	# Gyroscope
	# =================================== #
	cU = np.cos(g[i][0]/2)
	cV = np.cos(g[i][1]/2)
	cW = np.cos(g[i][2]/2)
	sU = np.sin(g[i][0]/2)
	sV = np.sin(g[i][1]/2)
	sW = np.sin(g[i][2]/2)

	q_gyr = [cU*cV*cW + sU*sV*sW, sU*cV*cW - cU*sV*sW, cU*sV*cW + sU*cV*sW, cU*cV*sW - sU*sV*cW]

	# =================================== #
	# Magnetometer
	# =================================== #
	Gamma = m[i][0]*m[i][0] + m[i][1]*m[i][1]
	if m[i][0] >= 0:
		q_mag = [np.sqrt(Gamma + m[i][0]*np.sqrt(Gamma))/np.sqrt(2*Gamma), 0, 0, m[i][1]/np.sqrt(2*(Gamma + m[i][0]*np.sqrt(Gamma)))]

	else:
		q_mag = [m[i][1]/np.sqrt(2*(Gamma - m[i][0]*np.sqrt(Gamma))), 0, 0, np.sqrt(Gamma - m[i][0]*np.sqrt(Gamma))/np.sqrt(2*Gamma)]

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
	a_g = np.matmul(R, np.transpose(a[i]))
	a_g[2] -= 9.81		#Removing gravity vector
	#print(f"x: {a_g[0]:.3f}  y: {a_g[1]:.3f}  z: {a_g[2]:.3f}")

# =================================================================== #
# ================= Integrating global acceleration ================= #
# ===================================================================
	v = integrate(v, a_g, timestep)
	s = integrate(s, v, timestep)

	print(s)

