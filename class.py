from distutils.dep_util import newer_group
import numpy as np


class rInputs:
    def __init__(self, conc, vflow,type,time):
        self.conc = conc
        self.vflow = vflow
        self.type = type
        self.time=time

    def flow(self):
        if self.type == "sin":
    
        elif self.type == "cos":

        elif self.type == "heaviside_step":

        elif self.type == "sigmoid":

        elif self.type == "modsin":

        elif self.type == "modcos":

        elif self.type == "linear_step":

        


    
class reactor:
    def __init__(self, conc, vflow,type,time):
        self.conc = conc
        self.vflow = vflow
        self.type = type
        self.time=time

    
# input
# r=r+newr
# g=g+newg
# b=b+newb

# generation
g+=0.7*r + 0.2*b - 0.85*g
b+=0.85*g -0.8*b
r+=0.6*b - 0.7*r

v+=newv
outv = max(v-v_max,0)

