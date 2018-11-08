import csv

def convert(str):
    bin_str = ''

    for i in range(0, len(str)):
        if(str[i] == '0'):
            bin_str = bin_str + '0000'
        elif(str[i] == '1'):
            bin_str += '0001'
        elif(str[i] == '2'):
            bin_str += '0010'
        elif(str[i] == '3'):
            bin_str += '0011'
        elif(str[i] == '4'):
            bin_str += '0100'
        elif(str[i] == '5'):
            bin_str += '0101'
        elif(str[i] == '6'):
            bin_str += '0110'
        elif(str[i] == '7'):
            bin_str += '0111'
        elif(str[i] == '8'):
            bin_str += '1000'
        elif(str[i] == '9'):
            bin_str += '1001'           
        elif(str[i] == 'a'):
            bin_str += '1010'
        elif(str[i] == 'b'):
            bin_str += '1011'
        elif(str[i] == 'c'):
            bin_str += '1100'
        elif(str[i] == 'd'):
            bin_str += '1101'
        elif(str[i] == 'e'):
            bin_str += '1110'
        elif(str[i] == 'f'):
            bin_str += '1111' 
        elif(str[i] == ''):
            pass
        elif(str[i] == '\t'):
            pass
        else:
            print("Invalid key")

    return bin_str

ReadFile = "C:/Users/HP/Desktop/Cheminformatics Datasets/CDK2_all-actives.txt"

def readFile(ReadFile):

    fname = ReadFile

    #To store the final elements without tabs and whitespaces
    alist2 = []         

    #To store the converted elemets
    alist3 = []        

    with open(ReadFile) as f:
        alist = f.read().splitlines()
    
    #Incorrect length of the list
    print(len(alist))               

    #Removing the empty character
    i = 0
    while i < len(alist):
        if(alist[i] == ''):
            alist.pop(i)
        else:   
            i += 1

    #Correct length of the list
    print(len(alist))

    #Removing the tabs
    for i in range(0, len(alist)):
        string = alist[i]
        if(string[len(string)-1] == '\t'):
            alist2.append(string.replace("\t", ""))
        else:
            alist2.append(string)
    
    for j in range(0, len(alist2)):
        binary_string = convert(alist2[j])
        alist3.append(binary_string)
    
    return alist3


if __name__ == '__main__':
    final = []
    final = readFile("C:/Users/HP/Desktop/Cheminformatics Datasets/CDK2_all-actives.txt")

    csvfile = "C:/Users/HP/Desktop/Cheminformatics Datasets/CDK2_binary.csv"

    with open(csvfile, "w+") as output:
        writer = csv.writer(output, lineterminator = '\n')
        writer.writerows(zip(final))

    print(final)
        