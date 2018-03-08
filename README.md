# RecipeTransformer

This python module takes in a URL pointing to a recipe from AllRecipes.com. It then promps the user to identify any and all supported 
transformations they would like to make to the recipe. These transformations can be any of the following 
	
* To and from vegetarian 
* To and from vegan
* To and from healthy 
* To and from pescatarian
* To Style of cuisine (i.e. to Thai)
* DIY to easy
* Cooking method (from bake to stir fry, for example)

The program then outputs a JSON representation of the new ingredients and changes made to the original recipe to accomplish these transformations. 


# Usage 

```python
# set URL variable to point to a AllRecipes.com url
URL = 'http://allrecipes.com/recipe/234667/chef-johns-creamy-mushroom-pasta/?internalSource=rotd&referringId=95&referringContentType=recipe%20hub'

# parse the URL to get relevant information
recipe_attrs = parse_url(URL) 		# parse_url returns a dict with data to populate a Recipe object
recipe = Recipe(**recipe_attrs)			# instantiate the Recipe object by unpacking dictionary

# apply a transformation
recipe_vegan = recipe.to_style('Mexican')	# convert the Creamy Mushroom Pasta to be Mexican style
recipe_vegan.print_pretty()				# print the new recipe 

```



# Classes

* **Recipe Class** is the main class in which all the transformation methods are. It also holds a list of Ingredient objects and Instruction objects parsed from the input recipe's URL (from allrecipes.com). It also finds the cooking tools and cooking methods used in the recipe by parsing the Instruction objects once they are instatiated and built. The Recipe class gets built by a dictionary object returned from `parse_url(URL)` function which scrapes the URL from allrecipes.com and returns a dictionary with all the necessary information to build the Recipe object. 

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;The Recipe class gets instatiated with a dictionary with the following schema:
<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{
	<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;name: string
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		preptime: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		cooktime: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		totaltime: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		ingredients: list of strings
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		instructions: list of strings
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		calories: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		carbs: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		fat: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		protien: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		cholesterol: int
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		sodium: int
<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}
<br />

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;and thus you can access information like `sodium` by calling recipe.sodium etc. The ingredients and instruction 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;lists are instatiated and parsed in the Recipe's `__init__` method.


* **Ingredient Class** is used to parse and store the Ingredients in a clean and easily accessible manner. An Instruction object takes in a string (the text of a bullet point from the recipe's url in the ingredients section) and parses out the name, quantity, measurement, descriptor, preperation, and type. It does this using NLTK's part of speech tagger as well as a word bank. The type is a single letter correlated to one of the following:
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* H --> Herbs / Spices
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* V --> Vegetable 
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* M --> Meat
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* D --> Dairy
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* F --> Fruit
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* S --> Sauce
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* P --> Pescatarian (Seafood)
		<br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;		* ? --> Misc.
		<br />
		<br />

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;This is done by building out lists parsed from websites like wikipedia.com and naturalhealthtechniques.com that 
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;have long records for each category. By tagging each ingredient with a type, we are able to infer a lot more about
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;the ingredient and it is integral to the Recipe's to_style method.


* **Instruction Class** is used to parse and store the Instructions in a clean and easily accessible manner. The `__init__` method calls other methods within the class to find the cooking methods and tools used in that instruction as well as the amount of time the instruction takes. It is important to store this in a different object than the Recipe class so that when we change the recipes, we can update the specific instrucitons and details accordingly.



# Methods

The following are the methods of the Recipe class

* to_vegan() - replaces non-vegan ingredients (meat, dairy, ect.) with vegan substitutes
* from_vegan() - replaces vegan ingredients with non-vegan ingredients like meat, dairy, ect. 
* to_vegetarian() - replaces non-vegetarian ingredients (meat) with vegetarian substitutes such as tofu and such. Updates the instructions and times accordingly
* from_vegetarian() - adds a random meat to the recipe and updates the instructions and times
* to_pescatarian() - replaces meats with seafood and/or adds new seafood ingredients to the recipe
* from_pescatarian() - replaces seafood with meat and/or adds new meat ingredients to the recipe
* to_style(style, threshold=1.0) - takes in a parameter of type string `style` (i.e. 'Mexican', 'Thai') and converts the recipe to be more of the input style. The parameter `threshold` allows the user to control how much they want their recipe changed to the desired style. Threshold is a float from 0.0 to 1.0 with 0.0 being no changes and 1.0 being as many changes as possible. 


# Dependencies 

* Used Python2.7 but works with Python3 as well. 
* BeautifulSoup
* NLTK
* Requests

