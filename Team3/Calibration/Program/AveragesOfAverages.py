import numpy as np


file = open("Averages.txt", "r")
A_x = []
A_y = []
A_z = []
G_x = []
G_y = []
G_z = []
M_x = []
M_y = []
M_z = []

A_xSTD = []
A_ySTD = []
A_zSTD = []
G_xSTD = []
G_ySTD = []
G_zSTD = []
M_xSTD = []
M_ySTD = []
M_zSTD = []

x = 0
for i in file:
	if x != 0:
		x = i.rsplit(sep="	")
		if len(x) >= 17:
			A_x.append(float(x[0]))
			A_y.append(float(x[1]))
			A_z.append(float(x[2]))
			G_x.append(float(x[3]))
			G_y.append(float(x[4]))
			G_z.append(float(x[5]))
			M_x.append(float(x[6]))
			M_y.append(float(x[7]))
			M_z.append(float(x[8]))
			A_xSTD.append(float(x[9]))
			A_ySTD.append(float(x[10]))
			A_zSTD.append(float(x[11]))
			G_xSTD.append(float(x[12]))
			G_ySTD.append(float(x[13]))
			G_zSTD.append(float(x[14]))
			M_xSTD.append(float(x[15]))
			M_ySTD.append(float(x[16]))
			M_zSTD.append(float(x[17]))
	else:
		x+=1

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

print("\n\n ==== STD ====")

print(f"A_x:", np.mean(A_xSTD))
print(f"A_y:", np.mean(A_ySTD))
print(f"A_z:", np.mean(A_zSTD))
print(f"G_x:", np.mean(G_xSTD))
print(f"G_y:", np.mean(G_ySTD))
print(f"G_z:", np.mean(G_zSTD))
print(f"M_x:", np.mean(M_xSTD))
print(f"M_y:", np.mean(M_ySTD))
print(f"M_z:", np.mean(M_zSTD))

print("\n\n ==== Biases ==== ")
print("\n		Acceleration		")
print(f"A_x: {A_xMean:.5f}  A_y: {A_yMean:.5f}  A_x: {(A_zMean - 9.81):.5f}  ")

print("\n		Gyroscropic		")
print(f"G_x: {G_xMean:.5f}  G_y: {G_yMean:.5f}  G_x: {G_zMean:.5f}  ")

	