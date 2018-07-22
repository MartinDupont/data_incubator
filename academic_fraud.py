# -*- coding: utf-8 -*-
"""
This code reads through a database of academic papers and constructs a
graph of academics who are connected by coautorship relations and citations. 

I create a selection of features, following the ideas put forward in:
https://www.andrew.cmu.edu/user/lakoglu/icdm12/ICDM12-Tutorial%20-%20PartI.pdf
The features measure traits related to the connectivity of each node. 
We then plot these features against each other, and try and find outliers. 
These outliers are those that have something unusual about the way they have 
been cited.

Code can be slow and resource-heavy. 
"""
from collections import defaultdict
import copy
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time

class BaseNode:
    pass

class PaperNode(BaseNode):
    def __init__(self, paper_id):
        self.paperid = paper_id
        self.cited_by = set() # list of strings
        self.cites = set()
        self.authors = set()

class AuthorNode(BaseNode):
    def __init__(self, author):
        self.author_name = author
        self.coauthors = set()
        self.n_papers = 0
        self.cited_by = set()
        self.cites = set()
        
    @property
    def bidirectional_citations(self):
        return  (self.cited_by | self.cites)



# =========================================================================== #
#               Read in Data and Construct Academic Graph
# =========================================================================== #

paper_tree = {}
author_tree = {}
max_len = 900000
#t 
with open("AMiner-Paper.txt", "r", encoding = "utf-8") as file:
    buffer = defaultdict(list)
    while len(author_tree) < max_len:
        line = file.readline()
        if line == "\n":
            continue
        thing = line.strip().split(" ")
        tag = thing[0]
        
        # We add lines into a buffer until we reach a new node, then we process
        # and reset the buffer. 
        if tag == "#index" and buffer:
            p_id = buffer["#index"][0]
            p_node = PaperNode(p_id)
            p_node.cites = set(buffer["#%"])
            paper_tree[p_id] = p_node
            authors = set(buffer["#@"][0].split(";"))
            authors.discard("") # trouble caused by split()
            p_node.authors = authors
            for a in authors:
                not_me = {b for b in authors if not(b == a)}
                if a in author_tree:
                    a_node = author_tree[a]
                    a_node.coauthors.update(not_me)
                    #a_node.papers.add(p_id)
                else:                   
                    a_node = AuthorNode(a)
                    a_node.coauthors = not_me
                    #a_node.papers.add(p_id)
                    author_tree[a] = a_node
            buffer = defaultdict(list)
 
        buffer[tag] += [" ".join(thing[1:])]
   
print("Number of papers read in: {}".format(len(paper_tree))) 
print("Number of Authors: {}".format(len(author_tree)))      
# consolidate Authors, complete all the edges by adding in a cited_by, and 
# cites relationsip. 
thing = copy.deepcopy(list(paper_tree.keys()))
# making a deepcopy because you can't modify a dictionary that you're iterating over.
# making a deepcopy of just the keys because i don't want to double the tree,
# that would kill my memory requirements.
for p_id in thing:
    node = paper_tree[p_id]
    a_nodes = [author_tree[n_a] for n_a in node.authors]
    for a_n in a_nodes:
        a_n.n_papers += 1 # should see if I can rearrange these loops
    for i in node.cites:
        if i in paper_tree: # some papers cite other papers which were not read in
            cited_authors = paper_tree[i].authors
            for a_n in a_nodes:
                #a_n.cites.update(cited_authors)
                for c in cited_authors:
                    if a_n.author_name != c:
                        c_node = author_tree[c]
                        c_node.cited_by.add(a_n.author_name)
                        a_n.cites.add(c)

thing = None
paper_tree = None
print("Finished building academic tree")
# =========================================================================== #
#                           Begin Data Analysis
# =========================================================================== #
all_attributes = []
count = 1
t = time.time()
for author, a_node in author_tree.items():
    if count % 1000 == 0:
        print("processing {}-th author ".format(count))
    
    #build coauthorship egonet
    co_authors = a_node.coauthors
    n_edges_coauthors = len(a_node.coauthors)
    for a in co_authors:
        new_edges = (co_authors & author_tree[a].coauthors)
        n_edges_coauthors += len(new_edges)
#        for c in author_tree[a].coauthors:
#            if (c in a_node.coauthors) and (c != author):
#                n_edges_coauthors +=1
                
    #build citation egonet
    n_edges_citations = len(a_node.bidirectional_citations)       
    for a in (a_node.bidirectional_citations):
        a_neighbours = author_tree[a].bidirectional_citations
        new_edges = (a_neighbours & a_node.bidirectional_citations)
        n_edges_citations += len(new_edges)
#        for c in author_tree[a].bidirectional_citations:
#            if (c in a_node.bidirectional_citations) and (c != a) and (c != author):
#                n_edges_citations +=1
    
    if len(a_node.cited_by) != 0: 
        score_citers =  len(a_node.cited_by & co_authors) / len(a_node.cited_by) 
    else:
        score_citers = 0 #benefit of the doubt
    
    if len(a_node.cites) != 0:
        score_citees =  len(a_node.cites & co_authors) / len(a_node.cites) 
    else:
        score_citees = 0 #benefit of the doubt
    
    if (len(a_node.cited_by) + len(a_node.cites)) == 0:
        citer_citee_ratio = 0
    else:
        citer_citee_ratio = len(a_node.cited_by & a_node.cites) / len(a_node.bidirectional_citations)

    all_attributes += [{"author":author, "N_citations":len(a_node.cited_by), "N_citees":len(a_node.cites),
                        "citations_ratio":score_citers, "citees_ratio":score_citees,
                        "N_papers":a_node.n_papers, "citer_citee_ratio":citer_citee_ratio,
                        "N_edges_coauthor_egonet":n_edges_coauthors, "N_coauthors":len(a_node.coauthors),
                        "N_bidirectional_cites":len(a_node.bidirectional_citations),
                        "N_edges_citation_egonet":n_edges_citations}]
    count += 1
 
diff = time.time()- t
print("Data processing time: {}".format(diff))
egonets = pd.DataFrame(all_attributes)  
#egonets = egonets[egonets["author"] != ""]

# =========================================================================== #
#                          Begin Making Plots
# =========================================================================== #

x = egonets["N_citations"]
y = egonets["N_citees"]
plt.figure()
plt.scatter(x,y)

numerical_cols = list(egonets.columns.values)
numerical_cols.remove("author")

folder = "pics/"
for i_1 in range(len(numerical_cols)):
    for i_2 in range(len(numerical_cols)):
        if i_1 > i_2:
            c_1 = numerical_cols[i_1]
            c_2 = numerical_cols[i_2]
            plt.figure()
            x = egonets[c_1]
            y = egonets[c_2]
            plt.scatter(x,y, alpha = 0.25)
            plt.xlabel(c_1)
            plt.ylabel(c_2)
            savestring = folder+c_1+"_"+c_2+".png"
            plt.savefig(savestring)
            plt.close()
        elif i_1 == i_2:
            try:
                plt.figure()
                c= numerical_cols[i_1]
                x = egonets[c]
                hist, edges = np.histogram(x, bins=100)
                plt.plot(edges[0:-1], np.log(hist))
                plt.xlabel(c)
                plt.ylabel("log count of {}".format(c))
                savestring = folder+c+".png"
                plt.savefig(savestring)
                plt.close()
            except:
                pass
                
            

#bool_arr = (egonets["N_bidirectional_cites"] < 220) & (egonets["N_edges_citation_egonet"] > 10000) & (egonets["N_bidirectional_cites"] > 120)
# n citations on n coauthors is a good ratio.
#x = egonets["N_bidirectional_cites"]
#y = egonets["N_edges_citation_egonet"]


# build egonet
#for author, a_node in author_name_dict.items():
    

    
    