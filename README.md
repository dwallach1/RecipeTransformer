# RecipeTransformer

This python module takes in a URL pointing to a recipe from AllRecipes.com. It then promps the user to identify any and all supported 
transformations they would like to make to the recipe. These transformations can be any of the following 
	
	* To and from vegetarian and/or vegan
	* Style of cuisine
	* To and from healthy (or perhaps even different types of healthy)
	* DIY to easy
	* Cooking method (from bake to stir fry, for example)

The program then outputs a JSON representation of the new ingredients and changes made to the original recipe to accomplish these transformations. 

# Dependencies 
	* Used Python2.7 but works with Python3 as well. 
	* BeautifulSoup