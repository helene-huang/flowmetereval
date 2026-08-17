import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("./roc_curve.csv")

plt.figure()
plt.plot(df['fpr'], df['tpr'], '-')
plt.draw()

plt.show()
