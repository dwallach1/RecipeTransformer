"""
Recipe Transformer Project

Given a URL to a recipe from AllRecipes.com, this program uses Natural Language Processing to transform any recipe, based on
user's input, into any or all of the following categories:  
	•   To and from vegetarian and/or vegan
	•   Style of cuisine
	•   To and from healthy (or perhaps even different types of healthy)
	•   DIY to easy
	•   Cooking method (from bake to stir fry, for example)


Authors: 
 	• David Wallach

"""

import requests
from bs4 import BeautifulSoup


class Recipe(object):
	"""
	Used to represent a recipe. Data for each recipe can be found 
	on AllRecipes.com. 
	"""
	def __init__(self):
		pass





def parse_url(url):
	"""
	reads the url and creates a recipe object.
	Urls are expected to be from AllRecipes.com
	"""

	# retrieve data from url
	result = requests.get(url)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")



