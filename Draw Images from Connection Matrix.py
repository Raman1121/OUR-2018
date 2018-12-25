import matplotlib.pyplot as plt
import matplotlib.cm as cm 
import numpy as np
import seaborn as sns
import os

def draw_image(filename):
    individual = filename.split('.')[0] + 'png'
    input_file = 'C:/Users/HP/Desktop/Cheminformatics Datasets/CDK2_all-actives_tables 2/' + filename
    output_file = 'C:/Users/HP/Desktop/Cheminformatics Datasets/Output Folder/' + individual
    myArray = np.loadtxt(input_file)
    ax = sns.heatmap(myArray, square=True, xticklabels=False, yticklabels=False, cbar=False, linewidths=.8, linecolor='lightgray', cmap='gray_r')
    figure = ax.get_figure()
    figure.savefig(output_file, dpi=400)

directory_in_str = 'C:/Users/HP/Desktop/Cheminformatics Datasets/CDK2_all-actives_tables 2'
directory = os.fsencode(directory_in_str)
outfolder = 'C:/Users/HP/Desktop/Cheminformatics Datasets/Output Folder/'

def iterate:
    for file in os.listdir(directory):
        filename = os.fsdecode(file)
        if filename.endswith(".txt"): 
            # print(os.path.join(directory, filename))
            Individual_file = filename.split('.')[0]
            #print(Individual_file)
            draw_image(filename)
            outfile = outfolder + filename.split('.')[0] + '.jpg'
            ##Image.save(outfile)
        
        else:
            print("File not available")
            continue


if __name__ == "__main__":
    iterate()
