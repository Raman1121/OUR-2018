import numpy as np
import os

directory_in_str = 'C:/Users/HP/Desktop/Cheminformatics Datasets/CDK2_all-actives_tables 2/'
directory = os.fsencode(directory_in_str)

result = np.zeros((67,67))

input_list = []

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".txt"): 
        complete_filename = directory_in_str + filename
        a = np.loadtxt(complete_filename)
        result[:a.shape[0],:a.shape[1]] = a
        print(result.shape)
        input_list.append(result)
        #print(complete_filename)
        #print(np.loadtxt(complete_filename).shape)
        continue
    else:
        continue


input_array = np.array(input_list)
