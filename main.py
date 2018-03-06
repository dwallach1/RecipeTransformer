"""
Recipe Transformer Project

Given a URL to a recipe from AllRecipes.com, this program uses Natural Language Processing to transform any recipe, based on
user's input, into any or all of the following categories:  
	*   To and from vegetarian and/or vegan
	*   Style of cuisine
	*   To and from healthy (or perhaps even different types of healthy)
	*   DIY to easy
	*   Cooking method (from bake to stir fry, for example)


Authors: 
 	* David Wallach

"""
import re
import json
from urlparse import urlparse
from collections import defaultdict
from operator import itemgetter
import requests
from bs4 import BeautifulSoup
from nltk import word_tokenize, pos_tag
import textwrap
 

DEBUG = False

measure_regex = '(cup|spoon|fluid|ounce|pinch|gill|pint|quart|gallon|pound)'
tool_indicator_regex = '(pan |skillet|pot |sheet|grate|whisk)'
method_indicator_regex = '(boil|bake|simmer|stir)'
time_indicator_regex = '(min)'

meats_regex = '(beef|steak|chicken|pork|bacon|fish|salmon|tuna|sausage)( (chop|steak|breast))?'
meat_sauces_regex = '(fish) (sauce)'
meat_stocks_regex = '(fish|chicken) (stock|broth)'
heat_method_indicator_regex = ('boil|bake|simmer|stir')

class Ingredient(object):
	"""
	Represents an Ingredient in the recipe. Ingredients have assoiciated quantities, names, measurements, 
	preperation methods (i.e. finley chopped), and descriptors (i.e. fresh, extra-virgin). Uses NLTK to tag each word's part 
	of speach using the pos_tag fuction. From there the module handles extracting out the relavent information and storing it in the appropiate
	attributes of the object.

	For pos_tag:
		* ADJ	adjective	new, good, high, special, big, local
		* ADP	adposition	on, of, at, with, by, into, under
		* ADV	adverb	really, already, still, early, now
		* CONJ	conjunction	and, or, but, if, while, although
		* DET	determiner, article	the, a, some, most, every, no, which
		* NOUN	noun	year, home, costs, time, Africa
		* NUM	numeral	twenty-four, fourth, 1991, 14:24
		* PRT	particle	at, on, out, over per, that, up, with
		* PRON	pronoun	he, their, her, its, my, I, us
		* VERB	verb
		* .	    punctuation marks	. , ; !
		* X	    other	ersatz, esprit, dunno, gr8, univeristy
	"""
	def __init__(self, description):
		description_tagged = pos_tag(word_tokenize(description))

		# if DEBUG:
		# 	print ('tags: {}'.format(description_tagged))

		self.name = self.find_name(description_tagged)
		self.quantity = self.find_quantity(description)				# do not use tagged description -- custom parsing for quantities
		self.measurement = self.find_measurement(description_tagged)
		self.descriptor = self.find_descriptor(description_tagged)
		self.preperation = self.find_preperation(description_tagged)

		if DEBUG:
			print ('parsing ingredient: {}'.format(description))
			print ('name: {}'.format(self.name))
			print ('quantity: {}'.format(self.quantity))
			print ('measurement: {}'.format(self.measurement))
			print ('descriptor: {}'.format(self.descriptor))
			print ('preperation: {}').format(self.preperation)
		

	def find_name(self, description):
		"""
		looks for name of the ingredient from the desciption. Finds the nouns that are not measurements
		"""
		name = [d[0] for d in description if (d[1] == 'NN' or d[1] == 'NNS' or d[1] == 'NNP') and not re.search(measure_regex, d[0])]
		if len(name) == 0:
			return description[-1][0]
		return ' '.join(name)


	def find_quantity(self, description):
		"""
		looks for amount descriptors in the ingredient description.
		if none are apparent, it returns zero. Else it converts fractions to floats and
		aggregates measurement (i.e. 1 3/4 --> 1.75)
		"""
		wholes = re.match(r'([0-9])\s', description)
		fractions = re.search(r'([0-9]\/[0-9])', description)

		if fractions: 
			fractions = fractions.groups(0)[0]
			num = float(fractions[0])
			denom = float(fractions[-1])
			fractions = num / denom
		
		if wholes: wholes = int(wholes.groups(0)[0])

		total = float(wholes or 0.0) + float(fractions or 0.0)

		return total


	def find_measurement(self, description):
		"""
		looks for measurements such as cups, teaspoons, etc. 
		Uses measure_regex which is a compilation of possible measurements.
		"""
		measurement = [d[0] for d in description if re.search(measure_regex, d[0])]
		return ' '.join(measurement)
	

	def find_descriptor(self, description):
		"""
		looks for descriptions such as fresh, extra-virgin by finding describing words such as
		adjectives
		"""
		# return candidates
		descriptors = [d[0] for d in description if (d[1] == 'JJ' or d[1] == 'RB') and not re.search(measure_regex, d[0])]
		return descriptors


	def find_preperation(self, description):
		"""
		find all preperations (finely, chopped) by finding action words such as verbs 
		"""
		preperations = [d[0] for d in description if d[1] == 'VB' or d[1] == 'VBD']
		for i, p in enumerate(preperations):
			if p == 'taste':
				preperations[i] = 'to taste'
		return preperations



class Instruction(object):
	"""
	Represents an instruction to produce the Recipe. Each instruction has a set of tools used for cooking and set of 
	methods also used for cooking. There is a time field to denote the amount of time the instruction takes to complete.
	"""
	def __init__(self, instruction):
		instruction = word_tokenize(instruction)
		self.cooking_tools = self.find_tools(instruction)
		self.cooking_methods = self.find_methods(instruction)
		self.time = self.find_time(instruction)


	def find_tools(self, instruction):
		"""
		looks for any and all cooking tools apparent in the instruction text by using the tool_indicator_regex
		variable
		"""
		cooking_tools = []
		for i, word in enumerate(instruction):
			if re.search(tool_indicator_regex, word):
				cooking_tools.append(instruction[i])
			
		return cooking_tools


	def find_methods(self, instruction):
		"""
		looks for any and all cooking methods apparent in the instruction text by using the method_indicator_regex
		variable
		"""
		cooking_methods = []
		tags = pos_tag(instruction)
		for i, word in enumerate(instruction):
			if re.search(method_indicator_regex, word):
				cooking_methods.append(instruction[i])

		cooking_methods.extend([word[0] for word in tags if word[1] in ['VB', 'VBD']])
			
		return cooking_methods


	def find_time(self, instruction):
		"""
		looks for all time notations apparent in the instruction text by using the time_indicator_regex
		variable and aggregating the total times using typecasting
		"""
		time = 0
		for i, word in enumerate(instruction):
			if re.search(time_indicator_regex, word):
				try:
					time += int(instruction[i-1])	
				except:
					pass
		return time



class Recipe(object):
	"""
	Used to represent a recipe. Data for each recipe can be found 
	on AllRecipes.com. 
	"""
	def __init__(self, **kwargs):
		for key, value in kwargs.items():
			setattr(self, key, value)

		self.text_instructions = self.instructions;		# store the original instructions, 
														# idea for right now is to modify the original instructions for transformations
		self.ingredients = [Ingredient(ing) for ing in self.ingredients]		# store ingredients in Ingredient objects
		self.instructions = [Instruction(inst) for inst in self.instructions]	# store instructions in Instruction objects
		self.cooking_tools, self.cooking_methods  = self.parse_instructions()	# get aggregate tools and methods apparent in all instructions
	

	def parse_instructions(self):
		"""
		Gathers aggregate data from all instructions to provide overall cooking tools and methods instead of 
		per instruction basis
		"""
		cooking_tools =  []
		cooking_methods = []
		for inst in self.instructions:
			cooking_tools.extend(inst.cooking_tools)
			cooking_methods.extend(inst.cooking_methods)
		return list(set(cooking_tools)), list(set(cooking_methods))
		

	def print_pretty(self):
		"""
		convert representation to easily parseable JSON format
		"""
		data = {}
		data['name'] = self.name
		data['cooking tools'] = self.cooking_tools
		data['cooking method'] = self.cooking_methods
		ing_list = []
		for ingredient in self.ingredients:
			ing_attrs = {}
			for attr, value in ingredient.__dict__.iteritems():
				ing_attrs[attr] = value
			ing_list.append(ing_attrs)

		data['ingredients'] = ing_list
		parsed = json.dumps(data, indent=4, sort_keys=True)
		print (parsed)
		return parsed


	def print_recipe(self):
		"""
		print a human friendly version of the recipe
		"""
		print('\nIngredients List:')
		for ing in self.ingredients:			
			# only add quantity, measurement, descriptor, and preperation if we have them
			quant = ''
			if ing.quantity != 0:
				quant = "{} ".format(round(ing.quantity, 2) if ing.quantity % 1 else int(ing.quantity))

			measure = ''
			if ing.measurement != "":
				measure = ing.measurement + ' '

			descr = ''
			if len(ing.descriptor) > 0:
				descr = ' '.join(ing.descriptor) + ' '
			
			prep = ''
			if len(ing.preperation) > 0:
				prep = ', ' + ' and '.join(ing.preperation)
			
			full_ing = '{}{}{}{}{}'.format(quant, measure, descr, ing.name, prep)

			print(full_ing)

		print('\nInstructions:')
		for i, t_inst in enumerate(self.text_instructions[:-1]):
			print(textwrap.fill('{}. {}'.format(i+1, t_inst), 80))


	def to_vegan(self):
		"""
		"""
		pass


	def from_vegan(self):
		"""
		"""
		pass


	def to_vegetarian(self):
		"""
		Replaces meat or seafood ingredients with vegetarian alternatives. Directly replaces 
		each ingredient without changing the actual cooking style. 
		"""
		for ing in self.ingredients:
			meat_match = re.search(meats_regex, ing.name, re.I)

			# replace any meat stocks with veggie stocks, fish sauce with soy sauce, and 
			# meat with some amount of tofu
			if re.search(meat_stocks_regex, ing.name, re.I):
				for i, inst in enumerate(self.text_instructions):
					self.text_instructions[i] = re.sub(meat_stocks_regex, r'vegetable \2', inst)
				ing.name = re.sub(meat_stocks_regex, r'vegetable \2', ing.name)

			elif re.search(meat_sauces_regex, ing.name, re.I):
				for i, inst in enumerate(self.text_instructions):
					self.text_instructions[i] = re.sub(meat_sauces_regex, r'soy \2', inst)
				ing.name = re.sub(meat_stocks_regex, r'soy \2', ing.name)

			elif meat_match:
				meat_ing = meat_match.group(0)
				print meat_ing
				for i, inst in enumerate(self.text_instructions):
					self.text_instructions[i] = re.sub(meat_ing, 'tofu', inst)

				ing.name = 'tofu'
				ing.descriptor = []
				ing.preperation = []

				if 'ounce' in ing.measurement:
					pass
				elif re.search('pounds?\s', ing.measurement):
					ing.quantity /= 16.
				elif self.protien:
					ing.quantity = float(self.protien) / 4.
				else:
					ing.quantity = 8 

				ing.measurement = 'ounce' if ing.quantity == 1 else 'ounces'

		# remove any meat terms we missed and 'tofus' artifacts
		for i, inst in enumerate(self.text_instructions):
			new_inst = re.sub(meats_regex, 'tofu', inst)
			self.text_instructions[i] = re.sub('tofus', 'tofu', new_inst)


	def from_vegetarian(self):
		"""
		Adds chicken to the recipe
		"""
		self.ingredients.append(Ingredient('4 skinless, boneless chicken breast halves'))

		boiling_chicken = 'Place the chicken breasts in a non-stick pan and fill the pan with water until the breasts are covered.' \
		+ ' Simmer uncovered for 5 minutes.' \
		+ ' Then, turn off the heat and cover for 15 minutes. Remove the breasts and set aside.'
		adding_chicken = 'Shred the chicken breasts by pulling the meat apart into thin slices by hand. Stir in the shredded chicken.'
		self.text_instructions.insert(0, boiling_chicken)
		self.text_instructions.insert(-1, adding_chicken)


	def to_style(self, style):
		"""
		search all recipes for mexican recipes and build frequency dictionary and then add ingredients
		"""

		url = 'https://www.allrecipes.com/search/results/?wt={}&sort=re'.format(style)

		# retrieve data from url
		result = requests.get(url, timeout=10)
		c = result.content

		# store in BeautifulSoup object to parse HTML DOM
		soup = BeautifulSoup(c, "lxml")

		# find all urls that point to recipe pages 
		recipes = [urlparse(url['href']) for url in soup.find_all('a', href=True)]
		recipes = [r.geturl() for r in recipes if r.path[1:8] == 'recipe/']		# filter out noise urls 
		recipes = list(set(recipes))

		# parse the urls and create new Recipe objects
		recipes = [Recipe(**parse_url(recipe)) for recipe in recipes]
		print ('found {} recipes cooked {} style'.format(len(recipes), style))

		ingredients_ = [recipe.ingredients for recipe in recipes]
		ingredients = []
		for ingredient in ingredients_:
			ingredients.extend(ingredient)
		
		ingredients = [ingredient.name for ingredient in ingredients]

		key_ingredients = self.freq_dist(ingredients)
		# print (key_ingredients)


	def freq_dist(self, data):
		"""
		builds a frequncy distrobution dictionary sorted by the most commonly occuring words 
		"""
		freqs = defaultdict(lambda: 0)
		for d in data:
			d = d.split(' ')
			for w in d:
				freqs[w] += 1

		return sorted(freqs.items(), key=itemgetter(1), reverse=True)


def remove_non_numerics(string): return re.sub('[^0-9]', '', string)


def parse_url(url):
	"""
	reads the url and creates a recipe object.
	Urls are expected to be from AllRecipes.com


	Builds a dictionary that is passed into a Recipe object's init function and unpacked.
	The dictionary is set up as 

	{
		name: string
		preptime: int
		cooktime: int
		totaltime: int
		ingredients: list of strings
		instructions: list of strings
		calories: int
		carbs: int
		fat: int
		protien: int
		cholesterol: int
		sodium: int

	}
	"""
	# retrieve data from url
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")


	# find name 
	name = soup.find('h1', {'itemprop': 'name'}).text
	
	# find relavent time information
	# some recipes are missing some of the times 
	try: preptime  = remove_non_numerics(soup.find('time', {'itemprop': 'prepTime'}).text)
	except: preptime = 0
	try: cooktime  = remove_non_numerics(soup.find('time', {'itemprop': 'cookTime'}).text)
	except: cooktime = 0
	try: totaltime = remove_non_numerics(soup.find('time', {'itemprop': 'totalTime'}).text)
	except: totaltime = 0
	
	# find ingredients
	ingredients = [i.text for i in soup.find_all('span', {'class': 'recipe-ingred_txt added'})]

	# find instructions
	instructions = [i.text for i in soup.find_all('span', {'class': 'recipe-directions__list--item'})] 


	# nutrition facts
	calories = remove_non_numerics(soup.find('span', {'itemprop': 'calories'}).text)				
	carbs = soup.find('span', {'itemprop': 'carbohydrateContent'}).text			    # measured in grams
	fat = soup.find('span', {'itemprop': 'fatContent'}).text						# measured in grams
	protien  = soup.find('span', {'itemprop': 'proteinContent'}).text			    # measured in grams
	cholesterol  = soup.find('span', {'itemprop': 'cholesterolContent'}).text	    # measured in miligrams
	sodium  = soup.find('span', {'itemprop': 'sodiumContent'}).text			        # measured in grams

		
	if DEBUG:
		print ('recipe is called {}'.format(name))
		print ('prep time is {} minutes, cook time is {} minutes and total time is {} minutes'.format(preptime, cooktime, totaltime))
		print ('it has {} ingredients'.format(len(ingredients)))
		print ('it has {} instructions'.format(len(instructions)))
		print ('it has {} calories, {} g of carbs, {} g of fat, {} g of protien, {} mg of cholesterol, {} mg of sodium'.format(calories, carbs, fat, protien, cholesterol, sodium))


	return {
			'name': name,
			'preptime': preptime,
			'cooktime': cooktime,
			'totaltime': totaltime,
			'ingredients': ingredients,
			'instructions': instructions,
			'calories': calories,
			'carbs': carbs,
			'fat': fat,
			'protien': protien,
			'cholesterol': cholesterol,
			'sodium': sodium
			}


def user_input():
	"""
	Asks user what kind of transformations they would like to perform
	"""
	options = ['To vegetarian? (y/n) ', 'From vegetarian? (y/n) ', 'To healthy? (y/n) ', 'From healthy? (y/n) ']
	responses = []
	d = {'y': 1, 'n': 0}
	answered = False
	for opt in options:
		while not answered:
			try:
				ans = d[raw_input(opt)]
			except KeyError:
				continue
			else:
				answered = True
				responses.append(ans)
		answered = False
	return responses


def main():

	# url = raw_input('Enter a url from allrecipes.com: ')

	
	test_url = 'http://allrecipes.com/recipe/234667/chef-johns-creamy-mushroom-pasta/?internalSource=rotd&referringId=95&referringContentType=recipe%20hub'
	# test_url = 'http://allrecipes.com/recipe/21014/good-old-fashioned-pancakes/?internalSource=hub%20recipe&referringId=1&referringContentType=recipe%20hub'
	# test_url = 'https://www.allrecipes.com/recipe/60598/vegetarian-korma/?internalSource=hub%20recipe&referringId=1138&referringContentType=recipe%20hub'
	
	recipe_attrs = parse_url(test_url)
	recipe = Recipe(**recipe_attrs)

	recipe.to_style('mexican')
	# recipe.print_pretty()
	
	# recipe.to_vegetarian()
	# recipe.print_recipe()

	# transformations = user_input()
	# print (transformations)


if __name__ == "__main__":
	main()
