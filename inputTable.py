import numpy as np

x = np.linspace(0, 2*np.pi, num=200)

sin_arr = [np.sin(i) for i in x]
cos_arr= [np.cos(i) for i in x]
abs_sin_arr = [np.abs(np.sin(i)) for i in x]
abs_cos_arr= [np.abs(np.cos(i)) for i in x]
sigmoid_arr = [1/(1 + np.exp(-(i-np.pi)*3)) for i in x]

np.savetxt('tables.csv', (x, sin_arr,abs_sin_arr,cos_arr,abs_cos_arr,sigmoid_arr), delimiter=',')
