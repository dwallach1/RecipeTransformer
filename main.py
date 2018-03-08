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
import time
import random
import re
import json
from urlparse import urlparse
from collections import defaultdict
from operator import itemgetter
import requests
from bs4 import BeautifulSoup
from nltk import word_tokenize, pos_tag
import textwrap
import copy
 

DEBUG = False


# simple regex used to find specific attributes in strings 
measure_regex = '(cup|spoon|fluid|ounce|pinch|gill|pint|quart|gallon|pound)'
tool_indicator_regex = '(pan |skillet|pot |sheet|grate|whisk)'
method_indicator_regex = '(boil|bake|simmer|stir)'
heat_method_indicator_regex = ('boil|bake|simmer|stir')
time_indicator_regex = '(min)'



meats_regex = '(beef|steak|chicken|pork|bacon|fish|salmon|tuna|sausage)( (chop|steak|breast))?'
meat_sauces_regex = '(fish) (sauce)'
meat_stocks_regex = '(fish|chicken) (stock|broth)'



# start of word banks

healthy_substitutes = {
	# The way this dict is structures is so that the values are used to easily instatiate new Ingredient objects 
	# the quantities are just for parsing, they are updated to be the amount used of the unhealthy version in the recipe
	# inside the Recipe to_healthy method
	'oil': 	'2 tablespoons of Prune Puree',
	'cheese': '3 tablespoons of Nutritional Yeast',
	'pasta': '8 ounces of shredded zucchini',
	'flour': '1 cup of whole-wheat flour',
	'butter': '3 tablespoons of unsweetened applesauce',
	'cream': '3 cups of greek yogurt',


}

unhealthy_substitutes = {
	# The way this dict is structures is so that the values are used to easily instatiate new Ingredient objects 
	# the quantities are just for parsing, they are updated to be the amount used of the unhealthy version in the recipe
	# inside the Recipe to_healthy method
}

dairy_substitutes = {
	# The way this dict is structures is so that the values are used to easily instatiate new Ingredient objects 
	# the quantities are just for parsing, they are updated to be the amount used of the unhealthy version in the recipe
	# inside the Recipe to_healthy method
	'butter': '2 tablespoons of olive oil',
	'cheese': '3 tablespoons of yeast flakes',
	'milk': '12 ounces of soy milk',
	'sour cream': '2 avacados',
	'cream': '2 cups of almond milk yogurt',
	'ice cream': '2 cups of sorbet'

}

# do not need a dict because we switch based on 'type' attribute instead of 'name' attribute
meat_substitutes = ['1 cup Tofu', '1 cup ICantBelieveItsNotMeat']

# build list dynamically from wikipedia using the build_dynamic_lists() function -- used to tag the domain of an ingredient
sauce_list = []
vegetable_list = []
herbs_spice_list = []
dairy_list = []
meat_list = []
grain_list = []
fruit_list = []


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
		self.type = self.find_type()

		if DEBUG:
			print ('parsing ingredient: {}'.format(description))
			print ('name: {}'.format(self.name))
			print ('quantity: {}'.format(self.quantity))
			print ('measurement: {}'.format(self.measurement))
			print ('descriptor: {}'.format(self.descriptor))
			print ('preperation: {}').format(self.preperation)
	

	def __str__(self):
		"""
		"""
		return self.name


	def __repr__(self):
		"""
		"""
		return self.name


	def __eq__(self, other):
	    if isinstance(self, other.__class__):
	        return self.__dict__ == other.__dict__
	    return False


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


	def find_type(self):
		"""
		attempts to categorize ingredient for Recipe methods to work more smoothly and correctly

		* H --> Herbs / Spices
		* V --> Vegetable 
		* M --> Meat
		* D --> Dairy
		* F --> Fruit
		* S --> Sauce
		* ? --> Misc. 

		ordered by precedence of how telling the classification is --> bound to one classification
		"""
		types = ''
		if any(set(self.name.lower().split(' ')).intersection(set(example.lower().split(' '))) for example in meat_list) and len(types) == 0: types ='M' 
		if any(set(self.name.lower().split(' ')).intersection(set(example.lower().split(' '))) for example in vegetable_list) and len(types) == 0: types = 'V'
		if any(set(self.name.lower().split(' ')).intersection(set(example.lower().split(' '))) for example in dairy_list) and len(types) == 0: types = 'D' 
		if any(set(self.name.lower().split(' ')).intersection(set(example.lower().split(' '))) for example in grain_list) and len(types) == 0: types = 'G'
		if any(set(self.name.lower().split(' ')).intersection(set(example.lower().split(' '))) for example in sauce_list) and len(types) == 0: types = 'S'
		if any(set(self.name.lower().split(' ')).intersection(set(example.lower().split(' '))) for example in herbs_spice_list) and len(types) == 0: types = 'H'
		if any(set(self.name.lower().split(' ')).intersection(set(example.lower().split(' '))) for example in fruit_list) and len(types) == 0: types = 'F' 
		if len(types) == 0: types = '?'
		return types


class Instruction(object):
	"""
	Represents an instruction to produce the Recipe. Each instruction has a set of tools used for cooking and set of 
	methods also used for cooking. There is a time field to denote the amount of time the instruction takes to complete.
	"""
	def __init__(self, instruction):
		self.instruction = instruction
		self.instruction_words = word_tokenize(self.instruction)
		self.cooking_tools = self.find_tools(self.instruction_words)
		self.cooking_methods = self.find_methods(self.instruction_words)
		self.time = self.find_time(self.instruction_words)


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


	def update_instruction(self):
		"""
		"""
		self.instruction = ' '.join(self.instruction_words)


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

		# save original copy to compare with the transformations
		self.original_recipe = copy.deepcopy(self)
	

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
		

	def print_pretty(self, original=False):
		"""
		convert representation to easily parseable JSON format
		"""
		data = {}
		if original: self = self.original_recipe
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


	def compare_to_original(self):
		"""
		Compares the current recipe to the original recipe the object was instatiated with.
		If no changes were made, then they will be identical. 
		"""
		print ('-----------------------')
		print ('The following changes were made to the original recipe: ')
		if len(self.original_recipe.ingredients) < len(self.ingredients):
			for i in range(len(self.original_recipe.ingredients), len(self.ingredients)):
				print ('* added {}'.format(self.ingredients[i].name))
		else:
			for i in range(len(self.original_recipe.ingredients)):
				if self.original_recipe.ingredients[i].name != self.ingredients[i].name:
					print ('* {} ---> {}'.format(self.original_recipe.ingredients[i].name, self.ingredients[i].name))
		print ('-----------------------')


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


	def to_healthy(self):
		"""
		Transforms the recipe to a more healthy version by removing and/or replacing unhealthy ingredients
		"""
		for i, ingredient in enumerate(self.ingredients):
			if any(name in ingredient.name.split(' ') for name in healthy_substitutes.keys()):
				key = next(name for name in ingredient.name.split(' ') if name in healthy_substitutes.keys())
				healthy_sub = Ingredient(healthy_substitutes[key])
				healthy_sub.quantity = ingredient.quantity
				self.swap_ingredients(self.ingredients[i], healthy_sub)
		
		self.name = self.name + ' (healthy)'


	def from_healthy(self):
		"""
		Transforms the recipe to a less healthy (more delicous) version by adding unhealthy ingredients and/or replacing 
		healthy ingredients
		"""
		for i, ingredient in enumerate(self.ingredients):
			if any(name in ingredient.name.split(' ') for name in unhealthy_substitutes.keys()):
				key = next(name for name in ingredient.name.split(' ') if name in unhealthy_substitutes.keys())
				unhealthy_sub = Ingredient(healthy_substitutes[key])
				unhealthy_sub.quantity = ingredient.quantity
				self.swap_ingredients(self.ingredients[i], unhealthy_sub)
		
		self.name = self.name + ' (unhealthy)'
		

	def to_vegan(self):
		"""
		Transforms the recipe to be vegan by removing and/or subsituting all ingredients that are not vegan
		"""
		# start by making vegetarian
		self.to_vegetarian()

		# add a random dairy from the dairy_substitutes dictionary
		for i, ingredient in enumerate(self.ingredients):
			if ingredient.type == 'D':
				idx = random.randint(0, len(dairy_substitutes.keys()) - 1)
				dairy_sub = Ingredient(dairy_substitutes[dairy_substitutes.keys()[idx]])
				dairy_sub.quantity = ingredient.quantity
				self.swap_ingredients(self.ingredients[i], dairy_sub)
		
		self.name = self.name + ' (vegan)'


	def from_vegan(self):
		"""
		Transforms the recipe to be non-vegan by adding ingredients that are not vegan
		"""
		# start by adding random meat
		self.from_vegetarian()

		# find random dairy
		idx = random.randint(0, len(dairy_list) - 1)
		dairy = dairy_list[idx]

		# add it to the ingredients list
		self.ingredients.append(Ingredient('3 cups of {}'.format(dairy)))

		# create and add new instructions for making and inserting the dairy
		self.name = self.name + ' (non-vegan)'


	def to_vegetarian(self):
		"""
		Replaces meat or seafood ingredients with vegetarian alternatives. Uses a random integer generator to randomly choose
		which substitute from the meat_substitutes list to use. 
		"""

		for i, ingredient in enumerate(self.ingredients):
			if ingredient.type == 'M':
				idx = random.randint(0, len(meat_substitutes) - 1)
				meat_sub = Ingredient(meat_substitutes[idx])
				meat_sub.quantity = ingredient.quantity
				self.swap_ingredients(self.ingredients[i], meat_sub)
		
		self.name = self.name + ' (vegetarian)'


	def from_vegetarian(self):
		"""
		Adds a random meat from the gloabl meat_list to the recipe, updates instructions and times
		accordingly
		"""

		# find a random meat from the meat_list to add
		idx = random.randint(0, len(meat_list) - 1)
		meat = meat_list[idx]
		self.ingredients.append(Ingredient('3 cups of boiled {}'.format(meat)))


		# update/add/build the necessary instructions
		boiling_meat = 'Place the {} in a non-stick pan and fill the pan with water until the {} are covered.'.format(meat, meat) \
		+ ' Simmer uncovered for 5 minutes.' \
		+ ' Then, turn off the heat and cover for 15 minutes. Remove the breasts and set aside.'
		adding_meat = 'Shred the {} by pulling the meat apart into thin slices by hand. Stir in the shredded {}.'.format(meat, meat)

		# Instatiate objects
		boiling_meat_instruction = Instruction(boiling_meat)
		adding_meat_instruction = Instruction(adding_meat)


		# add the instructions to the recipe
		self.instructions.insert(0, boiling_meat_instruction)
		self.instructions.insert(-1, adding_meat_instruction)


	def to_style(self, style, threshold=1.0):
		"""
		search all recipes for recipes pertaining to the 'style' parameter and builds frequency dictionary.
		Then adds/removes/augemnets ingredients to make it more like the 'style' of cuisine. 
		"""

		url = 'https://www.allrecipes.com/search/results/?wt={}&sort=re'.format(style)

		# retrieve data from url
		result = requests.get(url, timeout=10)
		c = result.content

		# store in BeautifulSoup object to parse HTML DOM
		soup = BeautifulSoup(c, "lxml")

		# find all urls that point to recipe pages 
		style_recipes = [urlparse(url['href']) for url in soup.find_all('a', href=True)]	# find all urls in HTML DOM
		style_recipes = [r.geturl() for r in style_recipes if r.path[1:8] == 'recipe/']		# filter out noise urls 
		style_recipes = list(set(style_recipes))											# don't double count urls 

		# parse the urls and create new Recipe objects
		style_recipes = [Recipe(**parse_url(recipe)) for recipe in style_recipes]	# instantiate all recipe objects for each found recipe
		print ('found {} recipes cooked {} style'.format(len(style_recipes), style))

		# unpack all ingredients in total set of new recipes of type 'style'
		ingredients_ = [recipe.ingredients for recipe in style_recipes]
		ingredients = []
		for ingredient in ingredients_:
			ingredients.extend(ingredient)
		
		# hold reference to just the ingredient names for frequency distrobutions
		ingredient_names = [ingredient.name for ingredient in ingredients]

		# hold reference to ingredients from original recipe
		current_ingredient_names = [ingredient.name for ingredient in self.ingredients]
		# print ('current ingredients from original recipe are {}'.format(current_ingredient_names))

		# extract only the names and not the freqs -- will be sorted in decreasing order
		key_new_ingredients = [freq[0] for freq in self.freq_dist(ingredient_names)]
		# remove the ingredients that are already in there
		key_new_ingredients = [ingredient for ingredient in key_new_ingredients if not(ingredient in current_ingredient_names)][:10]
		# print ('key ingredients from {} recipes found are {}'.format(style, key_new_ingredients))


		# get the whole ingredient objects -- this is to change actions accorgingly
		# e.g. if we switch from pinches of salt to lemon, we need to change pinches to squeezes
		ingredient_changes = [ingredient for ingredient in ingredients if (ingredient.name in key_new_ingredients) and not(ingredient.name in current_ingredient_names)]
		
		# clear up some memory
		del ingredients_
		del ingredients
		del ingredient_names
		del style_recipes
		del soup


		tmp = []
		new = []
		for ingredient in ingredient_changes:
			if ingredient.name in tmp: continue
			tmp.append(ingredient.name)
			new.append(ingredient)

		ingredient_changes = copy.deepcopy(new)
		
		# no longer needed --> temporary use
		del new
		del tmp


		# Find out most common ingredients from all recipes of type 'style' -- then decide which to switch and/or add to current recipe
		try: most_common_sauce = next(ingredient for ingredient in ingredient_changes if ingredient.type == 'S')
		except StopIteration: most_common_sauce = None 
		try: most_common_meat = next(ingredient for ingredient in ingredient_changes if ingredient.type == 'M')
		except StopIteration: most_common_meat = None
		try: most_common_vegetable = next(ingredient for ingredient in ingredient_changes if ingredient.type == 'V')
		except StopIteration: most_common_vegetable = None
		try: most_common_grain = next(ingredient for ingredient in ingredient_changes if ingredient.type == 'G')
		except StopIteration: most_common_grain = None
		try: most_common_dairy = next(ingredient for ingredient in ingredient_changes if ingredient.type == 'D')
		except StopIteration: most_common_dairy = None
		try: most_common_herb = next(ingredient for ingredient in ingredient_changes if ingredient.type == 'H')
		except StopIteration: most_common_herb = None
		try: most_common_fruit = next(ingredient for ingredient in ingredient_changes if ingredient.type == 'F')
		except StopIteration: most_common_fruit = None
		

		# switch the ingredients
		most_commons = filter(lambda mc: mc != None, 
					[most_common_meat, most_common_vegetable, most_common_sauce, most_common_grain, 
					 most_common_herb, most_common_dairy, most_common_fruit])

		try: most_commons = most_commons[:int(7*threshold)]
		except: pass # this means we didnt find enough to choose -- just keep whole list b/c under threshold anyways

		# print ('most commons {}'.format([m.name for m in most_commons]))


		for new_ingredient in most_commons:
			try: current_ingredient = next(ingredient for ingredient in self.ingredients if ingredient.type == new_ingredient.type)
			except StopIteration: continue
			self.swap_ingredients(current_ingredient, new_ingredient)

		# update name
		self.name = self.name + ' (' + style + ')'


	def freq_dist(self, data):
		"""
		builds a frequncy distrobution dictionary sorted by the most commonly occuring words 
		"""
		freqs = defaultdict(lambda: 0)
		for d in data:
			freqs[d] += 1
		return sorted(freqs.items(), key=itemgetter(1), reverse=True)


	def swap_ingredients(self, current_ingredient, new_ingredient):
		"""
		replaces the current_ingredient with the new_ingredient. Updates the associated instructions, times, and ingredients. 
		"""
		# (1) switch the ingredients in self.ingredients list
		for i, ingredient in enumerate(self.ingredients):
			if ingredient.name == current_ingredient.name:
				self.ingredients[i] = new_ingredient

		# (2) update the instructions that mention it
		name_length = len(current_ingredient.name.split(' '))
		for i, instruction in enumerate(self.instructions):
			for j in range(len(instruction.instruction_words) - name_length):
				if current_ingredient.name == ' '.join(instruction.instruction_words[j:j+name_length]):
					self.instructions[i].instruction_words[j] = new_ingredient.name

					# get rid of any extra words
					for k in range(1, name_length):
						self.instructions[i].instruction_words[j+k] == ''
					self.instructions[i].update_instruction()
					
					# print ('--> looking for {}'.format(new_ingredient.name))
					# print (':: {}'.format(self.instructions[i].instruction))

		# (3) change the time if necessary

		# do not think we will implement -- requires tracking times from each of the freq dist which will take too much time + space
		


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


def build_dynamic_lists():
	"""
	fills the lists of known foods from websites -- used to tag ingredients 
	"""
	global vegetable_list
	global sauce_list
	global herbs_spice_list
	global dairy_list
	global meat_list
	global grain_list
	global fruit_list

	# build vegetable list
	url = 'https://simple.wikipedia.org/wiki/List_of_vegetables'
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")

	lis = [li.text.strip() for li in soup.find_all('li')]
	lis_clean = []
	for li in lis:
		if li == 'Lists of vegetables': break
		if len(li) == 1: continue
		if re.search('\d', li): continue
		if re.search('\n', li): continue
		lis_clean.append(li.lower())
	vegetable_list = lis_clean


	# build herbs and spices list
	url = 'https://en.wikipedia.org/wiki/List_of_culinary_herbs_and_spices'
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")

	lis = [li.text.strip() for li in soup.find_all('li')][3:]
	lis_clean = []
	for li in lis:
		if len(li) == 1: continue
		if re.search('\d', li): continue
		if re.search('\n', li): continue
		if li == 'Category': break
		lis_clean.append(li.lower())
	herbs_spice_list = lis_clean


	# build sauces list
	url = 'https://en.wikipedia.org/wiki/List_of_sauces'
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")

	lis = [li.text.strip() for li in soup.find_all('li')]
	lis_clean = []
	for li in lis:
		if len(li) == 1: continue
		if re.search('\d', li): continue
		if re.search('\n', li): continue
		if li == 'Category': break
		lis_clean.append(li.lower())
	sauce_list = lis_clean


	# build meat list
	url = 'http://naturalhealthtechniques.com/list-of-meats-and-poultry/'
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")

	div = soup.find('div', {'class': 'entry-content'})
	lis = [li.text.strip() for li in div.find_all('li')]
	lis_clean = []
	for li in lis:
		if len(li) == 1: continue
		if re.search('\d', li): continue
		if re.search('\n', li): continue
		lis_clean.append(li.lower())
	meat_list = lis_clean


	# build dairy list
	url = 'http://naturalhealthtechniques.com/list-of-cheese-dairy-products/'
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")

	div = soup.find('div', {'class': 'entry-content'})
	lis = [li.text.strip() for li in div.find_all('li')]
	lis_clean = []
	for li in lis:
		if len(li) == 1: continue
		if re.search('\d', li): continue
		if re.search('\n', li): continue
		lis_clean.append(li.lower())
	dairy_list = lis_clean


	# build grains list 
	url = 'http://naturalhealthtechniques.com/list-of-grains-cereals-pastas-flours/'
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")

	div = soup.find('div', {'class': 'entry-content'})
	lis = [li.text.strip() for li in div.find_all('li')]
	lis_clean = []
	for li in lis:
		if len(li) == 1: continue
		if re.search('\d', li): continue
		if re.search('\n', li): continue
		lis_clean.append(li.lower())
	grain_list = lis_clean


	# build grains list 
	url = 'http://naturalhealthtechniques.com/list-of-fruits/'
	result = requests.get(url, timeout=10)
	c = result.content

	# store in BeautifulSoup object to parse HTML DOM
	soup = BeautifulSoup(c, "lxml")

	div = soup.find('div', {'class': 'entry-content'})
	lis = [li.text.strip() for li in div.find_all('li')]
	lis_clean = []
	for li in lis:
		if len(li) == 1: continue
		if re.search('\d', li): continue
		if re.search('\n', li): continue
		lis_clean.append(li.lower())
	fruit_list = lis_clean


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts))
        else:
            print '%r  %2.2f s' % \
                  (method.__name__, (te - ts))
        return result
    return timed


@timeit
def main():
	"""
	main function -- runs all initalization and any methods user wants 
	"""
	# parse websites to build global lists -- used for Ingredient type tagging
	build_dynamic_lists()

	# test_url = 'http://allrecipes.com/recipe/234667/chef-johns-creamy-mushroom-pasta/?internalSource=rotd&referringId=95&referringContentType=recipe%20hub'
	# test_url = 'http://allrecipes.com/recipe/21014/good-old-fashioned-pancakes/?internalSource=hub%20recipe&referringId=1&referringContentType=recipe%20hub'
	test_url = 'https://www.allrecipes.com/recipe/60598/vegetarian-korma/?internalSource=hub%20recipe&referringId=1138&referringContentType=recipe%20hub'
	
	recipe_attrs = parse_url(test_url)
	recipe = Recipe(**recipe_attrs)

	recipe.from_vegetarian()
	# recipe.to_vegetarian()
	# recipe.to_healthy()
	# recipe.to_style('Mexican')
	recipe.print_pretty()
	recipe.compare_to_original()



if __name__ == "__main__":
	main()
