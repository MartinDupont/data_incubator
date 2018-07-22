# -*- coding: utf-8 -*-
"""
Created on Sat Jul 21 13:04:18 2018

@author: martin
"""
from collections import defaultdict
import copy
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

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
        self.papers = set()

# =========================================================================== #
#               Read in Data and Construct Academic Graph
# =========================================================================== #

paper_id_dict = {}
author_name_dict = {}
with open("AMiner-Paper.txt", "r", encoding = "utf-8") as file:
    count = 0
    buffer = defaultdict(list)
    for line in file:
        if line == "\n":
            continue
        thing = line.strip().split(" ")
        tag = thing[0]
        #print(line.strip().split(" "))

 
        # We add lines into a buffer until we reach a new node, then we process
        # and reset the buffer. 
        if tag == "#index" and buffer:
            p_id = buffer["#index"][0]
            p_node = PaperNode(p_id)
            p_node.cites = set(buffer["#%"])
            paper_id_dict[p_id] = p_node
            authors = set(buffer["#@"][0].split(";"))
            p_node.authors = authors
            for a in authors:
                not_me = {b for b in authors if not(b == a)}
                if a in author_name_dict:
                    a_node = author_name_dict[a]
                    a_node.coauthors.update(not_me)
                    a_node.papers.add(p_id)
                else:                   
                    a_node = AuthorNode(a)
                    a_node.coauthors = not_me
                    a_node.papers.add(p_id)
                    author_name_dict[a] = a_node
            buffer = defaultdict(list)
 
        buffer[tag] += [" ".join(thing[1:])]
        count += 1
        if count > 5000000:
            break
        
# consolidate papers, complete all the edges by adding in a cited_by, 
# and also adding in papers that are cited, but weren't read in. 
thing = copy.deepcopy(list(paper_id_dict.keys()))
for p_id in thing:
    node = paper_id_dict[p_id]
    for i in node.cites:
        if not(i in paper_id_dict):
            p_node = PaperNode(i)
            paper_id_dict[i] = p_node
        else:
            p_node = paper_id_dict[i]
        p_node.cited_by.add(i)
    
thing = None

# building a citations/citation by graph amongst the authors, derived from the
# paper citations. 
# Allows for easier searchinng.
for author, a_node in author_name_dict.items():
    a_node.cited_by = set()
    a_node.cites = set()
    for paper_id in a_node.papers:
        paper = paper_id_dict[paper_id]
        for p_id in paper.cited_by:
            p_node = paper_id_dict[p_id]
            authors_cited_by = p_node.authors
            a_node.cited_by.update(iter(authors_cited_by))
            
        for p_id in paper.cites:
            p_node = paper_id_dict[p_id]
            authors_cited = p_node.authors
            a_node.cites.update(iter(authors_cited))
    
    a_node.bidirectional_edges = (a_node.cites | a_node.cited_by)
    

# =========================================================================== #
#                           Begin Data Analysis
# =========================================================================== #
all_attributes = []
for author, a_node in author_name_dict.items():
    co_authors = set(a_node.coauthors)
    
    #build coauthorship egonet
    n_edges_coauthors = len(a_node.coauthors)
    for a in a_node.coauthors:
        for c in author_name_dict[a].coauthors:
            if (c in a_node.coauthors) and (c != a) and (c != author):
                n_edges_coauthors +=1
                
    #build citation egonet
    n_edges_citations = len(a_node.bidirectional_edges)       
    for a in (a_node.bidirectional_edges):
        for c in author_name_dict[a].bidirectional_edges:
            if (c in a_node.bidirectional_edges) and (c != a) and (c != author):
                n_edges_citations +=1
    
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
        citer_citee_ratio = len(a_node.cited_by & a_node.cites) / len(a_node.bidirectional_edges)

    all_attributes += [{"author":author, "N_citations":len(a_node.cited_by), "N_citees":len(a_node.cites),
                        "citations_ratio":score_citers, "citees_ratio":score_citees,
                        "N_papers":len(a_node.papers), "citer_citee_ratio":citer_citee_ratio,
                        "N_edges_coauthor_egonet":n_edges_coauthors, "n_coauthors":len(a_node.coauthors),
                        "N_bidirectional_cites":len(a_node.bidirectional_edges),
                        "N_edges_citation_egonet":n_edges_citations}]
 
egonets = pd.DataFrame(all_attributes)    
egonets = egonets[egonets["author"] != ""]

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
    

    
    