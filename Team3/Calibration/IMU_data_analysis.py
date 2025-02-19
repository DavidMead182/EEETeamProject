import numpy as np
import matplotlib.pyplot as plt
Data=open("IMU_Rotation.txt", "r")
#Data=open("IMU_Stationary.txt", "r")

#cd ./Documents/CoolTerm/NoLabels
#python3 IMU_data_analysis.py

# =============== Initialising arrays =============== #

A_x = []
A_y = []
A_z = []
G_x = []
G_y = []
G_z = []
M_x = []
M_y = []
M_z = []

# =============== Extracting values =============== #

for i in Data:
	x = i.rsplit(sep=",")
	A_x.append(float(x[0]))
	A_y.append(float(x[1]))
	A_z.append(float(x[2]))
	G_x.append(float(x[3]))
	G_y.append(float(x[4]))
	G_z.append(float(x[5]))
	M_x.append(float(x[6]))
	M_y.append(float(x[7]))
	M_z.append(float(x[8]))

# =============== Print averages =============== #

A_xMean = np.mean(A_x)
A_yMean = np.mean(A_y)
A_zMean = np.mean(A_z)
G_xMean = np.mean(G_x)
G_yMean = np.mean(G_y)
G_zMean = np.mean(G_z)
M_xMean = np.mean(M_x)
M_yMean = np.mean(M_y)
M_zMean = np.mean(M_z)


print(f"\n\n ====  MEAN  ==== ")
print(f"A_x:", A_xMean)
print(f"A_y:", A_yMean)
print(f"A_z:", A_zMean)
print(f"G_x:", G_xMean)
print(f"G_y:", G_yMean)
print(f"G_z:", G_zMean)
print(f"M_x:", M_xMean)
print(f"M_y:", M_yMean)
print(f"M_z:", M_zMean)

# =============== Adjusting using bias =============== #
for i in range(len(A_x)):
	A_x[i] -= A_xMean
	A_y[i] -= A_yMean
	A_z[i] -= A_zMean
	G_x[i] -= G_xMean
	G_x[i] -= G_yMean
	G_x[i] -= G_zMean
	M_x[i] -= M_xMean
	M_x[i] -= M_yMean
	M_x[i] -= M_zMean


# =============== Standard deviation =============== #

print(f"\n\n ====  STANDARD DEVIATION  ==== ")
print(f"A_x:{np.std(A_x)} ")
print(f"A_y:{np.std(A_y)} ")
print(f"A_z:{np.std(A_z)} ")
print(f"G_x:{np.std(G_x)} ")
print(f"G_y:{np.std(G_y)} ")
print(f"G_z:{np.std(G_z)} ")
print(f"M_x:{np.std(M_x)} ")
print(f"M_y:{np.std(M_y)} ")
print(f"M_z:{np.std(M_z)} ")


	
