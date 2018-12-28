import cv2
import os
import numpy as np
from numpy import genfromtxt

h=150
w=150

for r in range(1,80):
    img = np.zeros((h,w,3), np.uint8)
    for py in range(0,h):
        for px in range(0,w):
            img[py][px][0]=255
            img[py][px][1]=255
            img[py][px][2]=255
    
    mt = genfromtxt("C:/pharm/"+str(r)+".txt", delimiter=' ')
    for i in range(0,len(mt)):
        for j in range(0,len(mt)):
                if mt[i][j] == 0:
                        img[i][j][0]=255
                        img[i][j][1]=255
                        img[i][j][2]=255
                elif mt[i][j] == 1:
                        img[i][j][0]=0
                        img[i][j][1]=0
                        img[i][j][2]=0
                elif mt[i][j] == 2:
                        img[i][j][0]=26
                        img[i][j][1]=0
                        img[i][j][2]=0
                elif mt[i][j] == 3:
                        img[i][j][0]=51
                        img[i][j][1]=0
                        img[i][j][2]=0
                elif mt[i][j] == 6:
                        img[i][j][0]=128
                        img[i][j][1]=128
                        img[i][j][2]=128
                elif mt[i][j] == 7:
                        img[i][j][0]=0
                        img[i][j][1]=0
                        img[i][j][2]=255
                elif mt[i][j] == 8:
                        img[i][j][0]=255
                        img[i][j][1]=0
                        img[i][j][2]=0
                elif mt[i][j] == 9:
                        img[i][j][0]=51
                        img[i][j][1]=204
                        img[i][j][2]=51
                elif mt[i][j] == 14:
                        img[i][j][0]=255
                        img[i][j][1]=102
                        img[i][j][2]=0
                elif mt[i][j] == 16:
                        img[i][j][0]=255
                        img[i][j][1]=255
                        img[i][j][2]=0
                elif mt[i][j] == 17:
                        img[i][j][0]=0
                        img[i][j][1]=102
                        img[i][j][2]=0
                elif mt[i][j] == 26:
                        img[i][j][0]=102
                        img[i][j][1]=102
                        img[i][j][2]=153
                elif mt[i][j] == 33:
                        img[i][j][0]=255
                        img[i][j][1]=153
                        img[i][j][2]=255
                elif mt[i][j] == 34:
                        img[i][j][0]=255
                        img[i][j][1]=153
                        img[i][j][2]=102
                elif mt[i][j] == 35:
                        img[i][j][0]=102
                        img[i][j][1]=0
                        img[i][j][2]=102
    
    cv2.imwrite(os.path.join(os.path.expanduser('~'),"Pictures",str(r)+".jpg"), img)

