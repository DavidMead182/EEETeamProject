import numpy as np

#GITHUB LINK
#https://github.com/Mayitzin/ahrs/blob/master/ahrs/filters/aqua.py

#cd ./Documents/Fourth year/TDP4/Readings
#python3 Initial_Dead_Reckoning_Test_quaternion.py

def integrate(x, dx, dt):
	return x + np.multiply(dx,dt)

# Function to compute the inverse of a quaternion
def quaternion_inverse(q):
    w, x, y, z = q
    norm_squared = w**2 + x**2 + y**2 + z**2
    conjugate = np.array([w, -x, -y, -z])
    return conjugate / norm_squared

# Function to multiply two quaternions
def quaternion_multiply(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 + y1*w2 + z1*x2 - x1*z2
    z = w1*z2 + z1*w2 + x1*y2 - y1*x2
    return np.array([w, x, y, z])

# Function to rotate the local acceleration to the global frame using the quaternion
def rotate_local_to_global(acc_local, q):
    # Convert local acceleration to quaternion (scalar part is 0)
    q_acc_local = np.array(acc_local.tolist() + [0])

    # Compute the inverse of the quaternion q
    q_inv = quaternion_inverse(q)

    # Perform the rotation: q * q_acc_local * q_inv
    q_acc_global = quaternion_multiply(quaternion_multiply(q, q_acc_local), q_inv)

    # The vector part of the resulting quaternion is the global acceleration
    return q_acc_global[1:]  # Return only the vector part

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

# =====================================
# Filter implementation
# =====================================

for i in range(len(a)):
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
# ============= Using quaternions to find acceleration ============== #
# =================================================================== #

	# Find the global acceleration
	a_g = rotate_local_to_global(a_l[i], q)

	#Removing g
	a_g[2] -= 9.81

# =================================================================== #
# ================= Integrating global acceleration ================= #
# ===================================================================
	v = integrate(v, a_g, timestep)
	s = integrate(s, v, timestep)

	print(f"Global:  x = {s[0]:.3f}  y = {s[1]:.3f}  z = {s[2]:.3f}")


