import re
# read sampledata/genera_list.txt
refined_genera_list = []

with open('sampledata/genera_list.txt', 'r') as f:
    genera_list = f.read().splitlines()
    for line in genera_list:
        genus, type_species, author, locality, family, age, comment = "", "", "", "", "", "", ""
        line = line.strip()
        line0 = line
        if line[-1] != ".":
            print("Error: The line does not end with a period.", line)
        # remove the period at the end of the line
        line = line[:-1]
        words = line.split(" ")
        genus = words[0]
        # remove genus from line
        line = line[len(genus):].strip()
        line1 = line

        author_end_position = line.find("[")
        if author_end_position > -1:
            author = line[:author_end_position].strip()
            line = line[author_end_position:]
        line1_5 = line
        # to find author, find the location of "[" and get the words after the genus name and before "[".
        type_species_found = re.search(r'(\[.*?\])', line)
        if type_species_found:
            type_species = type_species_found.group(1)
            #print(type_species)
            type_species_location = line.find(type_species)
            #author = line[:type_species_location].strip()
            type_species_words = type_species.split(" ")
            if len(type_species_words) > 1:
                comment_keywords = ["preocc", "j.o.s", "misspelling", "suppressed"]
                for keyword in comment_keywords:
                    if type_species.find(keyword) > -1:
                        comment = type_species
                        line = line.replace(type_species, "").strip()
                        type_species = ""
            line = line.replace(type_species, "").strip()
            type_species = type_species.replace("[","").replace("]","").strip()

        else:
            print("Error: No type species found.", line)
        if type_species and type_species != "":
            len_type_species = len(type_species)
        else:
            type_species = ""
            len_type_species = 0

        # remove front part up to type species from the line
        #if len_type_species > 0:
        #    line = line[type_species_location+len_type_species+1:]
        line2 = line

        #comment = ""
        comment_str = r"\[.*?\]"
        # get comment
        comment_found = re.search(comment_str, line)
        if comment_found:
            comment += comment_found.group(0)
            line = re.sub(comment_str, "", line)
            #print("comment:", comment)
            
        line = line.strip()
        line3 = line
        words = [ x.strip() for x in line.split(";") ]
        if len(words) == 3:
            locality, family, age = words
            #print("Normal", genus, "("+type_species+")", author, locality, family, age)
        elif len(words) == 1 and words[0] == "":
            # no info
            pass
            #print("Not normal 1:", genus, "["+type_species+"]", "author:", author, "words: [" + ",".join(words) + "]", comment)
            #print("line0:", line0)
            #print("line1:", line1)
            #print("line2:", line2)
            #print("line3:", line3)
        else:
            print("Not normal 2:", genus, type_species, "author:", author, "words: [" + ",".join(words) + "]", comment)
            print("line0:", line0)
            print("line1:", line1)
            print("line1.5:", line1_5)
            print("line2:", line2)
            print("line3:", line3)
        genus_info = [genus, type_species, author, locality, family, age, comment]
        refined_genera_list.append(genus_info)
        #refined_genera_list.append(genus+" ("+type_species+") "+author+"\n")
output_file = open('sampledata/trilobite_genera_list.txt', 'w')
for genus_info in refined_genera_list:
    # save as tsv
    output_file.write("\t".join(genus_info)+"\n")
output_file.close()

