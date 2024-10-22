import sys
sys.path.append('..')
sys.path.append('.')
from FgModel import *
import re
# read sampledata/genera_list.txt
systematic_description_authorship = {
    "A": "Ager, D. V",
    "AM": "Amsden, T. W",
    "B": "Biernat, Gertruda",
    "BO": "Boucot, A. J",
    "E": "Elliott, G. F",
    "G": "Grant, R. E",
    "H": "Hatai, Kotora",
    "J": "Johnson, J. G",
    "ML": "McLaren, D. J",
    "MW": "Muir-Wood, H. M",
    "P": "Pitrat, Charles W",
    "R": "Rowell, A. J",
    "SC": "Schmidt, Herta",
    "ST": "Staton, R. D",
    "S": "Stehli, F. G",
    "W": "Williams, Alwyn",
    "WR": "Wright, A. D"
}

phylum_Brachiopoda, created = FgTreeOfLife.get_or_create(name="Brachiopoda")
phylum_Brachiopoda.rank = "Phylum"
phylum_Brachiopoda.author = "Duméril, 1806"
phylum_Brachiopoda.year = "1806"
phylum_Brachiopoda.save()


refined_family_list = []
rank_order = ["Phylum", "Class", "Order", "Suborder", "Superfamily", "Family", "Subfamily", "Group", "Genus"]
parent_list = []
parent_list.append(phylum_Brachiopoda)
with open('sampledata/brachiopoda-suprafamilial.txt', 'r') as f:
    taxa_list = f.read().splitlines()
    for taxon_line in taxa_list:
        # find first "."
        #print(taxon_line)
        period_index = taxon_line.find(".")
        if period_index == -1:
            print("Error: no period.", taxon_line)
            continue
        if taxon_line.lower().find("uncertain") != -1 or taxon_line.lower().find("unknown") != -1:
            taxon_basic_list = taxon_line[:period_index].strip().split(" ")
            additional_info = taxon_line[period_index+1:].strip()
            rank = taxon_basic_list[0].replace("(","").replace(")","").replace(",","")
            genus_count = taxon_basic_list[-1].replace("(","").replace(")","")
            taxon_name = "Uncertain"
            #genus_count = taxon_basic_list[2].replace("(","").replace(")","")
            #print("Error: Uncertain found in the line.", taxon_line)
            #continue
        elif taxon_line.lower().find("doubtfully referred") != -1:
            print("Error: 'Doubtfully referred' found in the line.", taxon_line)
            continue
        else:
            taxon_basic_list = taxon_line[:period_index].strip().split(" ")
            additional_info = taxon_line[period_index+1:].strip()
            taxon_name = taxon_basic_list[0].replace(",","")
            if len(taxon_basic_list) > 2:
                genus_count = taxon_basic_list[2].replace("(","").replace(")","")
                rank = taxon_basic_list[1].replace("(","").replace(")","")
            elif len(taxon_basic_list) > 1:
                genus_count = taxon_basic_list[1].replace("(","").replace(")","")
                if taxon_name[-3:] == "dae":
                    rank = "Family"
                elif taxon_name[-3:] == "nae":
                    rank = "Subfamily"
                elif taxon_name[-3:] == "cea":
                    rank = "Superfamily"
        # in this text: U.Cam.-Ord. (R) find the last "(" and get the authorship
        authorship = ""
        author_info_list = []
        age = ""
        if additional_info.find("(") != -1:
            age = additional_info[:additional_info.rfind("(")].strip()
            authorship = additional_info[additional_info.rfind("(")+1:additional_info.rfind(")")]
            author_list = [ x.strip() for x in authorship.split(",") ]
            for author_name_abbr in author_list:
                if author_name_abbr in systematic_description_authorship:
                    author_info_list.append(systematic_description_authorship[author_name_abbr])
                else:
                    print("Error: authorship not found in the list.", taxon_line, author_name_abbr)
            #else:
            #    print("Error: authorship not found in the list.", taxon_line, authorship)
            #    authorship = ""
        else:
            print("no authorship found", taxon_line)
        if age == "":
            print("no age found", taxon_line)
        
        
        rank = rank.lower().capitalize()
        taxon_name = taxon_name.lower().capitalize()

        # get rank index from rank_order
        #print(rank_order, rank)
        rank_index = rank_order.index(rank)
        if len(parent_list) == 1:
            parent = phylum_Brachiopoda
        else:
            parent = parent_list[-1]
            parent_rank_index = rank_order.index(parent.rank)
            if rank_index > parent_rank_index:
                pass
                #new_taxon.parent = parent
                #new_taxon.save()
                #parent_list.append(new_taxon)
            elif rank_index == parent_rank_index:
                parent_list.pop()
                parent = parent_list[-1]
                #new_taxon.parent = parent_list[-1]
                #new_taxon.save()
                #parent_list[-1] = new_taxon
                #parent_list.append(new_taxon)
            else:
                while rank_index <= parent_rank_index:
                    #print("pop", parent_list[-1].name, rank_index, parent
                    parent_list.pop()
                    parent = parent_list[-1]
                    parent_rank_index = rank_order.index(parent.rank)
                    #parent_rank_index = rank_order.index(parent_list[-1][0])

        new_taxon, created = FgTreeOfLife.get_or_create(name=taxon_name, rank=rank, parent=parent)
        new_taxon.age = age
        new_taxon.comments = "Systematic description authorship: " + ", ".join(author_info_list)
        new_taxon.common_name = "Brachiopod"
        new_taxon.source = "Treatise of Invertebrate Paleontology, Part H, Brachiopoda, 1965"
        new_taxon.save()
        parent_list.append(new_taxon)
        #print(rank, taxon_name, genus_count)
        