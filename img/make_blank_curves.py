import matplotlib.pyplot as plt

fig = plt.figure(figsize=(20.0, 5.0))

ax1 = plt.subplot(1,2,1)
ax1.set(xlim = (0,6), ylim = (0,30))

ax2 = plt.subplot(1,2,2)
ax2.set(xlim = (0,6), ylim = (-60,60))
ax2.axhline(0, color = "black")

fig.savefig("pressure_time.png")

fig = plt.figure(figsize=(20.0, 5.0))

ax1 = plt.subplot(1,1,1)
ax1.set(xlim = (0,6), ylim = (0,500))
fig.savefig("volume_time.png")