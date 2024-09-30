import re
# read sampledata/genera_list.txt
with open('sampledata/genera_list.txt', 'r') as f:
    genera_list = f.read().splitlines()
    for line in genera_list:
        line = line.strip()
        if line[-1] != ".":
            print("Error: The line does not end with a period.", line)
        # Abadiella HUPE, 1953a [bourgini] Amouslek Fm, Morocco; ABADIELLIDAE; LCAM. 
        # this is an example. The genus name is Abadiella and the author is HUPE, 1953a. author and year are the words after the genus name and before "[".
        words = line.split(" ")
        genus = words[0]
        # to find author, find the location of "[" and get the words after the genus name and before "[".
        type_species = re.search(r'\[(.*?)\]', line)
        if type_species:
            type_species = type_species.group(1)
            type_species_location = line.find(type_species)
            author = line[len(genus):type_species_location-1].strip()
            #print(genus, "("+type_species+")", author)
        else:
            type_species = ""
        
        #exit

        
# refine the genera list
# write the refined genera list to sampledata/refined_genera_list.txt
