import re
# read sampledata/genera_list.txt
with open('sampledata/genera_list.txt', 'r') as f:
    genera_list = f.read().splitlines()
    for line in genera_list:
        line = line.strip()
        if line[-1] != ".":
            print("Error: The line does not end with a period.", line)
        # remove the period at the end of the line
        line = line[:-1]
        words = line.split(" ")
        genus = words[0]
        # to find author, find the location of "[" and get the words after the genus name and before "[".
        type_species = re.search(r'\[(.*?)\]', line)
        if type_species:
            type_species = type_species.group(1)
            #print(type_species)
            type_species_words = type_species.split(" ")
            if len(type_species_words) > 1:
                if type_species.find("preocc") > -1:
                    #print("preoccupied", line)
                    pass
                elif type_species.find("j.o.s") > -1:
                    #print("j.o.s", line)
                    pass
                else:
                    #print("type species error:", line)
                    pass
                continue
            else:
                type_species_location = line.find(type_species)
                author = line[len(genus):type_species_location-1].strip()
        else:
            print("Error: No type species found.", line)
            continue
        line = line[type_species_location+len(type_species)+1:]

        comment = ""
        comment_str = r"\[.*?\]"
        # get comment
        comment_find = re.search(comment_str, line)
        if comment_find:
            comment = comment_find.group(0)
            line = re.sub(comment_str, "", line)
            #print("comment:", comment)
            
        line = line.strip()
        words = [ x.strip() for x in line.split(";") ]
        if len(words) == 3:
            locality, family, age = words
            #print("Normal", genus, "("+type_species+")", author, locality, family, age)
        elif len(words) == 1 and words[0] == "":
            print("Not normal:", genus, "["+type_species+"]", author, comment)
        else:
            print("Not normal:", genus, "["+type_species+"]", author, words, comment)