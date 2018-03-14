$def with (form)

<html>
<form name="main" method="post"> 
$if not form.valid: <p class="error">Please try again</p>
$:form.render()
<input type="submit" />    </form>
</html>