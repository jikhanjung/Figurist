import re
# read sampledata/genera_list.txt
refined_family_list = []

with open('sampledata/family_list.txt', 'r') as f:
    family_list = f.read().splitlines()
    for line in family_list:
        family_name, author, author_info, year = "", "", "", ""
        line = line.strip()
        line0 = line
        if len(line)>0 and line[-1] != ".":
            print("Error: The line does not end with a period.", line)
        # remove the period at the end of the line
        line = line[:-1]
        words = line.split(" ")
        family_name = words[0]
        # remove family name from line
        line = line[len(family_name):].strip()
        line1 = line

        author_year_match = re.search(r'([\D]+)(,\s*)(\d{4})(\S*)', line)
        if author_year_match:
            author = author_year_match.group(1)
            comma = author_year_match.group(2)
            year = author_year_match.group(3)
            alpha = author_year_match.group(4)
            line = line.replace(author, "").strip()
            line = line.replace(comma, "").strip()
            line = line.replace(year, "").strip()
            line = line.replace(alpha, "").strip()
            #print(family_name,author, comma, year, alpha)
            author_info = f"{author}, {year}{alpha}"
        else:
            print("Error: No author and year found.", line0)
        
        line2 = line
        genera_list = line.split(",")
        genera_list = [genus.strip() for genus in genera_list]
        for genus in genera_list:
            pass
        
        refined_family_list.append([family_name, author_info, year])

output_file = open('sampledata/trilobite_family_list.txt', 'w')
for family_info in refined_family_list:
    output_file.write("\t".join(family_info)+"\n")
output_file.close()


