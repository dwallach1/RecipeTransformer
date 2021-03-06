# RecipeTransformer

This python module takes in a URL pointing to a recipe from AllRecipes.com. It then promps the user to identify any and all supported 
transformations they would like to make to the recipe. These transformations can be any of the following 
	
* To and from vegetarian 
* To and from vegan
* To and from healthy 
* To and from pescatarian
* To Style of cuisine (i.e. to Thai, Mexican, Italian, etc.)
* Cooking method (i.e. from bake to stirfry)
* DIY to easy 


The program then outputs a JSON representation of the new ingredients and changes made to the original recipe to accomplish these transformations. 

For grading purposes, here is what we completed:
 

- [x] Ingredient name
- [x] Quantity
- [x] Measurement (cup, teaspoon, pinch, etc.)
- [x] Descriptor (e.g. fresh, extra-virgin) (OPTIONAL)
- [x] Preparation (e.g. finely chopped) (OPTIONAL)
- [x] Tools – pans, graters, whisks, etc.
- [x] Primary cooking method (e.g. sauté, broil, boil, poach, etc.)
- [x] Other cooking methods used (e.g. chop, grate, stir, shake, mince, crush, squeeze, etc.) (OPTIONAL)
- [x] Steps – parse the directions into a series of steps that each consist of ingredients, tools, methods, and times (OPTIONAL)
- [x] To and from vegetarian (REQUIRED)
- [x] To and from healthy (REQUIRED)
- [x] Style of cuisine (AT LEAST ONE REQUIRED) 
- [x] Any input cuisine (OPTIONAL)
- [x] Another Style of cuisine (OPTIONAL)
- [x] to and from Pescatatian (OPTIONAL)
- [x] DIY to easy (OPTIONAL)
- [x] GUI to run the program (OPTIONAL)




# Usage 

```python
# set URL variable to point to a AllRecipes.com url
URL = 'http://allrecipes.com/recipe/234667/chef-johns-creamy-mushroom-pasta/?internalSource=rotd&referringId=95&referringContentType=recipe%20hub'

# parse the URL to get relevant information
recipe_attrs = parse_url(URL) 		# parse_url returns a dict with data to populate a Recipe object
recipe = Recipe(**recipe_attrs)			# instantiate the Recipe object by unpacking dictionary

# apply a transformation
recipe.to_style('Mexican')	# convert the Creamy Mushroom Pasta to be Mexican style
print(recipe.to_JSON())				# print the new recipe 
print(recipe.original_recipe.to_JSON)		# if you want to access the original recipe

```

If you prefer a GUI interface, we have implemented a locally hosted webpage using web.py. To run it, simply add the --gui flag in the command line: 
</br>
`>> python main.py --gui`
</br>
this will then print out a url to input into your webbrowser and from there you will be able to access all the functionality of this program and see the output in a much more friendly enviornment. 

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

* **to_vegan()** - replaces non-vegan ingredients (meat, dairy, ect.) with vegan substitutes
* **from_vegan()** - replaces vegan ingredients with non-vegan ingredients like meat, dairy, ect. 
* **to_vegetarian()** - replaces non-vegetarian ingredients (meat) with vegetarian substitutes such as tofu and such. Updates the instructions and times accordingly
* **from_vegetarian()** - adds a random meat to the recipe and updates the instructions and times
* **to_pescatarian()** - replaces meats with seafood and/or adds new seafood ingredients to the recipe
* **from_pescatarian()** - replaces seafood with meat and/or adds new meat ingredients to the recipe
* **to_style(style, threshold=1.0)** - takes in a parameter of type string `style` (i.e. 'Mexican', 'Thai') and converts the recipe to be more of the input style. The parameter `threshold` allows the user to control how much they want their recipe changed to the desired style. Threshold is a float from 0.0 to 1.0 with 0.0 being no changes and 1.0 being as many changes as possible. 
* **to_method(method)** - transforms the cooking method to be like that method. For example, if passed `'fry'` as the method paramter's value, then it will add flour and oil to the recipe if not already there and fry the meats and vegetables.
* **to_easy()** - transforms the recipe from DIY to easy by making the ingredients less intenaive to get and prepare
* **print_pretty()** - used to print the attributes of the recipe in an easy to read format
* **to_JSON()** - used to export the recipe class to a JSON format
* **compare_to_original()** - shows the additions and/or changes reflected in the current recipe from the recipe that the object was instatiated with


# Dependencies 

* Used Python2.7 but works with Python3 as well
* BeautifulSoup
* NLTK
* Requests
* web.py (for GUI)

# Program Architecture

![Program Architecture](./Program_Architecture.pdf)

