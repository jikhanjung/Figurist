import re
# read sampledata/genera_list.txt
refined_family_list = []
rank_order = ["Phylum", "Class", "Order", "Suborder", "Superfamily", "Family", "Subfamily", "Genus"]
parent_list = []
with open('sampledata/brachiopoda-suprafamilial.txt', 'r') as f:
    taxa_list = f.read().splitlines()
    for taxon_line in taxa_list:
        # find first "."
        #print(taxon_line)
        period_index = taxon_line.find(".")
        if period_index == -1:
            print("Error: The line does not end with a period.", taxon_line)
            continue
        if taxon_line.lower().find("uncertain") != -1 or taxon_line.lower().find("unknown") != -1:
            rank = taxon_line.strip().split(" ")[0].replace(",","")
            taxon_name = "Uncertain"
            #print("Error: Uncertain found in the line.", taxon_line)
            #continue
        else:
            taxon_basic_list = taxon_line[:period_index].strip().split(" ")
            taxon_name = taxon_basic_list[0]
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
        rank = rank.lower().capitalize()
        taxon_name = taxon_name.lower().capitalize()
        # get rank index from rank_order
        rank_index = rank_order.index(rank)
        if len(parent_list) == 0:
            parent_list.append([rank, taxon_name])
        else:
            parent_rank_index = rank_order.index(parent_list[-1][0])
            if rank_index > parent_rank_index:
                parent_list.append([rank, taxon_name])
            elif rank_index == parent_rank_index:
                parent_list[-1][1] = taxon_name
            else:
                while rank_index < parent_rank_index:
                    parent_list.pop()
                    parent_rank_index = rank_order.index(parent_list[-1][0])
                parent_list[-1][1] = taxon_name
            
        parent_rank = parent_list[-1][0]

        print(rank, taxon_name, genus_count)
        