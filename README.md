# Normalizing drug names to a single generic drug name

Requirements: MySQL version 5.5 and an account on MySQL. Make sure that mySQL has started on your computer (for Windows: check Services to see if the service has started).

This repository contains a module for normalizing drug names to one generic names. An adapted version of the RXNorm dictionary (UMLS) is used. This is a licensed database. A licence for downloading can be obtained at : https://www.nlm.nih.gov/databases/umls.html

Then download the newest version of the UMLS which includes MetamorphoSys
https://www.nlm.nih.gov/research/umls/licensedcontent/umlsknowledgesources.html

Use MetamorphoSys to load the files (approx 30 min)

Use the load scripts which you can request during this loading (explained below) to load UMLS into SQL): 
https://www.nlm.nih.gov/research/umls/implementation_resources/scripts/index.html

The transform_rxnorm_lexicon script (Python 2) can transform the rxnorm database into a dictionary that can be used with the DrugNorm class. There are two output files: a dictionary which allows for repeats in the name of a drug (e.g. gleevec pill gleevec) and one that does not. 

The DrugNorm script (Python 3) first subsets the dictionary for the drug names that are in your corpus and then uses simple matching to replace them by the generic drug name chosen as a key in the dictionary. 

These tools were originally developed for dealing with medical social media.
