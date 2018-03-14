$def with (form)

<html>
<head>
<title>Recipe Transformer</title>
<style>
body {
    background-color: linen;
    font-family: sans-serif;
}

h1 {
    color: maroon;
    margin-top: 40px;
    margin-left: 40px;
} 

h3 {
  margin-left: 40px;
} 

form {
	position: absolute;
   top: 50%;
   left: 50%;
   transform: translate(-50%, -50%);
   text-align: right;
}
div {
	margin: 0 auto;
	width: 400px;
	height: 100px;
	background-color: white;
	border: 1px black solid;
	position: relative;
}
.submit {
	margin-top: 1em;

}

</style>
</head>
<body>
	<h1>Recipe Transformer</h1>
	<h3><em>Take any recipe from allrecipes.com and modify how you like!</em><h3>
	<div>
    <form name="main" method="post">
        $:form.render()
        <input type="submit" class="submit" />
    </form>
    </div>
</body>
</html>