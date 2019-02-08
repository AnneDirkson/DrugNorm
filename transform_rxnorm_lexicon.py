
# coding: utf-8

# # Creating a rxnorm lexicon of generic and brand drug names

# --author -- AR Dirkson
# 
# --Python v2.7-- 
# 
# In this script, the RxNorm database is used to create a list for spelling correction and to create a drug name normalization lexicon. RxNorm is part of the UMLS and requires you to load only the RxNorm during the MetamorphoSys download.
# 
# First apply for a license to access the UMLS: https://www.nlm.nih.gov/databases/umls.html
# 
# Then download the newest version of the UMLS which includes MetamorphoSys
# https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html
# 
# Use MetamorphoSys to load the files (approx 30 min)
# 
# Use the load scripts which you can request during this loading (explained below) to load UMLS into SQL): 
# https://www.nlm.nih.gov/research/umls/implementation_resources/scripts/index.html
# 
# Requirements: MySQL version 5.5 and an account on MySQL. Make sure that mySQL has started on your computer (for Windows: check Services to see if the service has started).
# 
# For the normalization lexicon, only the first chemical names is taken as the key for the dictionary (the word you normalize to) and other chemical names and all brand names are used for the values (the words you want to normalize). Any ambiguous terms, defined as: terms that occur in more than 1 category, are removed.

# In[1]:


from collections import Counter
import MySQLdb
import pandas as pd
import re
from nltk import word_tokenize
import csv
import pickle


# # Connecting to SQL Server RxNorm database
#  
# Retrieving all strings which are connected to the relation 'has_tradename'

# In[2]:


db = MySQLdb.connect(host="localhost",
                             user="root",
                             passwd="yourpasswd",
                             db="rxnorm")

cursor = db.cursor()


# In[6]:


sql = "SELECT cui1, cui2 FROM mrrel WHERE RELA = 'has_tradename';"
cursor.execute(sql)

generic_drugs = []
brandnames = []

for row in cursor.fetchall():
    drug = row[1]
    generic_drugs.append(drug)
    brand = row[0]
    brandnames.append(brand)


# In[7]:


print(generic_drugs [0:10])
print(brandnames [0:10])

print(type(generic_drugs[0]))
print(type(brandnames[0]))

g = pd.DataFrame (generic_drugs)
b = pd.DataFrame (brandnames)
lex = pd.concat ((g,b), axis = 1)

lex.columns = ["Generic drug ID", "Brand name ID"]

print (lex.iloc [0:10])

print (lex.iloc [-10:])

print(len(lex))


# In[8]:


#check if there are Nan values in the lists
lex.isnull().sum()


# Replace the IDs for generic and brand name drugs

# In[ ]:


#retrieve the primary name 

generic_drugs_names = []

for id in lex ["Generic drug ID"]: 
    #print (id)
    query = id 
    query = repr(query).replace("'", "\'").replace('"', '\"')
    sql = "SELECT STR FROM mrconso WHERE cui = {};".format(query)
    cursor.execute(sql)

    generic_drugs_names.append(cursor.fetchone())
            
len(generic_drugs_names)
       


# Retrieving alternative generic drug names

# In[ ]:


alternative_names = [0]*len(lex)

for z, id in enumerate (lex["Generic drug ID"]):
    query = id 
    query = repr(query).replace("'", "\'").replace('"', '\"')
    sql = "SELECT STR FROM mrconso WHERE cui = {};".format(query)
    cursor.execute(sql)
    
    temp_list = []
    
    for i, row in enumerate (cursor.fetchall ()):
        if i == 0: 
            next
        else: 
            drug = row[0]
            temp_list.append (drug)
            #if i ==3: 
                #print (z)
    
    alternative_names[z] = temp_list
        


# In[ ]:


print(alternative_names[550])

print(generic_drugs_names[550])

## lengths should be the same

print(len(generic_drugs_names))

print(len(alternative_names))


# Retrieving brand names

# In[ ]:


drug_brandnames = [0]*len(lex)

for z, id in enumerate (lex ["Brand name ID"]):
    query = id 
    query = repr(query).replace("'", "\'").replace('"', '\"')
    sql = "SELECT STR FROM mrconso WHERE cui = {};".format(query)
    cursor.execute(sql)
    
    temp_list = []
    
    for i, row in enumerate (cursor.fetchall ()):
        drug = row[0]
        temp_list.append (drug)
        #if i ==3: 
           # print (z)
    
    drug_brandnames[z] = temp_list


# In[ ]:


print (drug_brandnames[0])
print (generic_drugs_names [0])
print (drug_brandnames [54])
print (generic_drugs_names [54])

print(len(drug_brandnames))


# _Making a dictionary out of the seperate lists_

# Preprocessing the keys (the first generic drug name) - removing details of dosage and administration method
# 

# In[ ]:


## word lists ## 

list_of_dosages = ['mg/ml', 'mg/mg', 'mci/ml', 'ml', 'mg', 'gm', 'gbq', 'mcg/actuat', 'actuat', 'mci'
                   , 'mw', 'sq-hdm', 'meq/ml', 'meq', 'mcg']

list_of_extra_words = [' oral', ' solution', ' suspension', ' injection', ' table', ' extract', 
                       ' whole', ' product', ' release', ' topical', ' ointment',' prefilled', ' syringe', ' chewable',
                      ' extended', ' oil', ' spray', ' gel', ' taper', ' medicated', ' patch'
                      , ' pack', ' cream', ' dose', ' metered', ' pill', ' shampoo', ' rinse', ' ingredients',
                      ' inhaler', ' sublingual', ' capsule', ' soap', ' liquid', ' powder', ' lotion', ' mask', ' masque']

#the space at the start of the word ensures that the word is not part of a bigger word but a space after the word would mean 
#that words at the end of a sentence would not be removed. 

list_of_time_words = [' per ', ' hour ', ' -hr ', ' hr ' ' -day ', ' day ', ' -week ', ' week ', ' -month ', ' month ']
#these words are more likely to be part of bigger words so they need a space after and before them

##cleaning functions ##
def first_clean (text0): 
    text1 = re.sub('\s\[[a-zA-Z0-9_\/ -]+\]', '', text0)  #remove extra information in [] and ()
    text2 = re.sub('\s\([a-zA-Z0-9_\/ -]+\)', '', text1) 
    text3 = re.sub(r'[\+\*#\!\?;><\^@\|\.=&%\(\)$~_§\\:\…\"\[\]´`\,\'\'""…¨\{\}]+', '', text2) #remove punctuation
    return text3

def word_split (corpus, corpus2): #corpus is the original, corpus2 is the one you are writing to
    for a, i in enumerate (corpus):
        temp = i.split (' / ')
        for y, z in enumerate (temp): 
            if y == 0: 
                corpus2.append (z)
            if y > 0: 
                extra.append (z)
                extra_num.append (a)

def lex_word_removal (text0, word): #remove unnecessary words
    text1 = text0.replace (word, '')
    return text1

def lex_word_removal_space (text0, word): #remove unnecessary words that need to replaced with a space
    text1 = text0.replace (word, ' ')
    return text1

#remove extra spacing and words likely to occur as start of drug names so need extra space
def post_split_clean (text0): 
    text1 = text0.replace (' in ', ' ') #remove the word in
    text2 = text1.replace ('/', '') # remove additional / 
    text3= re.sub('(([^-]|\A)[\d]+([^-]|\Z))',' ', text2)  #remove digits that are not attached to words with a hyphen
    text4= text3.replace ('  ', ' ') #remove double spacing
    text5 = re.sub('(\A\s|\s\Z)', '', text4) #remove spacing at the end or beginning of strings
    return text5


# In[ ]:


generic_drugs_names2 = []

for token in generic_drugs_names: 
    token1 = str(token)
    token2 = token1.lower()
    generic_drugs_names2.append(token2)                     

generic_drugs_names2 = [first_clean(m) for m in generic_drugs_names2]  
    
generic_drugs_names_spl = []
extra = []
extra_num = []

word_split(generic_drugs_names2, generic_drugs_names_spl)


# In[ ]:


print(len(generic_drugs_names2))
print(len(generic_drugs_names_spl))
print(len(extra))
print(len(extra_num))

print (extra[0:10])
print(extra_num[0:10])


# In[ ]:


for word in list_of_dosages: 
    print (word) 
    generic_drugs_names_spl = [lex_word_removal (m, word) for m in generic_drugs_names_spl]
    extra = [lex_word_removal (m, word) for m in extra]

for word in list_of_time_words: 
    print (word) 
    generic_drugs_names_spl = [lex_word_removal_space (m, word) for m in generic_drugs_names_spl]
    extra = [lex_word_removal (m, word) for m in extra]

#make a seperate list of first generic drug names with application method included to use as values
generic_drug_names_first_wappl = generic_drugs_names_spl

#only remove the type of application in the generic drug names that will function as keys

for word in list_of_extra_words: 
    print (word) 
    generic_drugs_names_spl = [lex_word_removal (m, word) for m in generic_drugs_names_spl] 
    
#last cleaning function
    
generic_drugs_names_spl = [post_split_clean(m) for m in generic_drugs_names_spl]
generic_drug_names_first_wappl = [post_split_clean(m) for m in generic_drug_names_first_wappl]
extra = [post_split_clean(m) for m in extra]


# In[ ]:


print(len(extra))
print(len(extra_num))


# Preprocessing the alternative drug names and brand names 

# In[ ]:


#concatenate the alternative and brand names

alt_names_total = [0]*len(alternative_names)

for i in range (len(alternative_names)): 
    alt_names_total [i] = alternative_names[i] + drug_brandnames [i]


# In[ ]:


print(alternative_names[54])
print(drug_brandnames [54])
print(alt_names_total [54])


# In[ ]:


#lower the words 
alt_names_total2 = []

for row in alt_names_total:
    for a, word in enumerate (row):
        word1 = word.lower ()
        row[a] = word1
    alt_names_total2.append(row)

z= alt_names_total2[0]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))
            
print(len(alt_names_total))
print(len(alt_names_total2))


# In[ ]:


#first preprocessing step: first_clean
alt_names_total3 = []

for row in alt_names_total2: 
    row2 = [first_clean(m) for m in row] 
    alt_names_total3.append(row2)
            
print(len(alt_names_total3))
print(len(alt_names_total2))

z= alt_names_total3[54]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))


# In[ ]:


#split the words with / between them
alt_names_total_spl = []

def word_split_alt (corpus, corpus2): #corpus is the original, corpus2 is the one you are writing to
    for a, row in enumerate (corpus):
        temp2 = []
        for b, word in enumerate(row):
            temp = word.split (' / ')
            temp2.append(temp)
        flat_temp2 = [item for sublist in temp2 for item in sublist]
        corpus2.append(flat_temp2)

word_split_alt(alt_names_total3, alt_names_total_spl)


# In[ ]:


print(len(alt_names_total2))
print(len(alt_names_total3))
print(len(alt_names_total_spl))

z= alt_names_total_spl[54]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))


# In[ ]:


# This appends the other generic names split from the first generic name (stored in extra) 
# to the list of alternative names that already exist.
print(alt_names_total_spl[38])

for a, i in enumerate (extra):
    y = extra_num[a]
    alt_names_total_spl[y].append (i)
    
#This appends the version of the first generic names with application method included to the list of values

for a, i in enumerate (generic_drug_names_first_wappl):
    alt_names_total_spl[a].append (i)
    
print(alt_names_total_spl[38]) 


# In[ ]:


z= alt_names_total_spl[38]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))


# In[ ]:


#Preprocessing after the splitting of words with post_split_clean function 

alt_names_total_spl2 = alt_names_total_spl

for word in list_of_dosages: 
    print (word) 
    for a,i in enumerate (alt_names_total_spl2): 
        i = [lex_word_removal (m, word) for m in i]
        alt_names_total_spl2[a] = i
        
for a, i in enumerate(alt_names_total_spl2): 
    i = [post_split_clean(m) for m in i]
    alt_names_total_spl2[a] = i


# In[ ]:


print(alt_names_total_spl2 [54])


# Get rid of duplicates in generic drug names 

# In[ ]:


norm_dict_gen_nodup = []
kept_list = []
removed_list = []
removed_list_due_to = []

def remove_dupl_special(corp, new_corp): #to enable syncing need to enumerate what is kept 
    for a, i in enumerate (corp): 
        if i in new_corp: 
            removed_list.append (a)
            for c, z in enumerate (corp): 
                if i == z: 
                    removed_list_due_to.append (c) 
                    break
        if i not in new_corp: 
            new_corp.append(i)    
            kept_list.append (a)

remove_dupl_special (generic_drugs_names_spl, norm_dict_gen_nodup)

print(len(generic_drugs_names_spl))
print(len(norm_dict_gen_nodup))


# In[ ]:


norm_dict_gen2 = generic_drugs_names_spl

print(norm_dict_gen2[11])
print(norm_dict_gen2[14])
print(norm_dict_gen2[13])
print(norm_dict_gen2[50])
print(norm_dict_gen2[121])

##yeeey it seems to work 


# Merge the medication names for the same generic drugs using 'removed list' - this is a list of all the chemical names that were not included as keys

# In[ ]:


print(alt_names_total_spl [38])

print(type(alt_names_total_spl))

print(type(alt_names_total_spl[0]))

for i in alt_names_total_spl2[-100]: 
    print (i)
    print(type(i))


# In[ ]:


norm_dict_alt = alt_names_total_spl2

for i in range (len(removed_list)):
    temp = []
    for z in norm_dict_alt[removed_list[i]]: 
        temp.append (z)
    for z in norm_dict_alt [removed_list_due_to[i]]: 
        temp.append (z)
    norm_dict_alt [removed_list_due_to[i]] = temp


# In[ ]:


print(len(alt_names_total_spl2[13]))
print(len(norm_dict_alt[13]))


# In[ ]:


#now we can remove the alternative names attached to the removed generic names 
norm_dict_alt2 = []

for i in range (len(kept_list)): 
     norm_dict_alt2.append(norm_dict_alt[kept_list[i]])
    
print(len(norm_dict_alt2))
print(len(norm_dict_gen_nodup))


# In[ ]:


z= norm_dict_alt2[38]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))
            


# Remove the duplicates within the lists 

# In[ ]:


test = ['boat', 'blue', 'moon', 'blue'], ['bag', 'red', 'bag', 'yellow']
test2 = []

for a in range(len(test)): 
    temp = []
    for i in test[a]: 
        if i not in temp:
            temp.append(i)
    test2.append(temp)
    
print(test2)


# In[ ]:


norm_dict_alt3 = []

for a in norm_dict_alt2: 
    temp = []
    for i in a: 
        if i not in temp:
            temp.append(i)
    norm_dict_alt3.append(temp)
    
# def remove_dupl(corp, new_corp): 
#     for i in corp: 
#         if i not in new_corp: 
#             new_corp.append(i)

print (len(norm_dict_alt3))
# print(norm_dict_alt3[13])


# In[ ]:


z= norm_dict_alt3[38]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))


# In[ ]:


norm_dict_alt_df  = pd.DataFrame (norm_dict_alt3)
norm_dict_alt_df.to_csv ('C:\\Users\\dirksonar\\Documents\\Data\\umls_extraction\\data\\norm_dict_alt_nodup.csv')


# In[ ]:


norm_dict_gen_nodup[0]


# Remove all from alternative names that are also in generic names 

# In[ ]:


def lex_word_removal (text0, word): #remove extra spacing and superfluous words
    text1 = text0.replace (word, '')
    return text1

norm_dict_alt4 = norm_dict_alt3

for word in norm_dict_gen_nodup: 
    for a, i in enumerate(norm_dict_alt3): 
        temp = []
        for token in i: 
            if token != word: 
                temp.append(token)
        norm_dict_alt4[a] = temp


# In[ ]:


z= norm_dict_alt4[38]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))


# Check for duplicates between the lists

# In[ ]:


#Counter on all words in a flat list and if any are more than 1 it is bad

norm_dict_alt4_flat = [word for sublist in norm_dict_alt4 for word in sublist]

from collections import Counter 

count = Counter(norm_dict_alt4_flat)

print(count.most_common(100))

# for i in list(count.values()): 
#     if i > 1: 
#         print ("Duplicate!")
#         print (i)


# Remove any ambiguous terms (so terms that are duplicates across different lists)

# In[ ]:


list_of_duplicate_keys =[]

z = list(count.keys())

for a, i in enumerate (list(count.values())): 
    if i > 1: 
        list_of_duplicate_keys.append(z[a])
        
#print(list_of_duplicate_keys)

x = len(list_of_duplicate_keys)
print(x)

y = len(count.keys())
print(y)

perc = (float(x)/float (y)*100)
print(perc)
        


# In[ ]:


for word in list_of_duplicate_keys: 
    for a, i in enumerate(norm_dict_alt4): 
        temp = []
        for token in i: 
            if token != word: 
                temp.append(token)
        norm_dict_alt4[a] = temp


# In[ ]:


def save_obj(obj, name):
     with open(name + '.pkl', 'wb') as f:
         pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

print(list_of_duplicate_keys[0:10])
save_obj(list_of_duplicate_keys, 'list_of_removed_ambiguous_terms')


# In[ ]:


len(norm_dict_alt4)

z= norm_dict_alt4[38]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))


# In[ ]:


#re-check if duplicates are gone 

norm_dict_alt4_flat2 = [word for sublist in norm_dict_alt4 for word in sublist]

from collections import Counter 

count2 = Counter(norm_dict_alt4_flat2)

#print(count2.most_common(100))

for i in list(count2.values()): 
    if i > 1: 
        print ("Duplicate!")
        print (i)


# Get rid of repeats in phrases

# In[ ]:


from nltk import word_tokenize 

norm_dict_alt5 = norm_dict_alt4

for a, li in enumerate (norm_dict_alt5): 
    li2 = []
    for phrase in li:
        phrase = word_tokenize (str(phrase))
        temp = []
        for word in phrase:
            if word not in temp: 
                temp.append (word)
        phrase = " ".join(temp)
        li2.append(phrase)
    norm_dict_alt5[a] = li2


# In[ ]:


print(len(norm_dict_alt4))
print(len(norm_dict_alt5))

z= norm_dict_alt5[38]
print(z)
print(type(z))
print(z[0])
print(type(z[0]))


# Creating the dictionary

# In[ ]:


drug_norm_dict = {}

for i in range (len(norm_dict_gen_nodup)): 
    drug_norm_dict[norm_dict_gen_nodup[i]] = norm_dict_alt4[i]


# In[ ]:


print(drug_norm_dict['imatinib'])


# In[ ]:


drug_norm_dict_no_rep = {}

for i in range (len(norm_dict_gen_nodup)): 
    drug_norm_dict_no_rep[norm_dict_gen_nodup[i]] = norm_dict_alt5[i]
    
print(drug_norm_dict_no_rep['imatinib'])


# In[ ]:


save_obj(drug_norm_dict, 'drug_normalize_dict')
save_obj(drug_norm_dict_no_rep, 'drug_normalize_dict_no_repeats')

