# Welcome to Microblog!

This is an example application featured in my [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world). See the tutorial for instructions on how to work with it.

Like most Flask extensions, you need to create an instance right after the Flask application is created. 

It is always best to move the application logic away from view functions and into models or other auxiliary classes or modules, because as you will see later in this chapter, that makes unit testing much easier.

The build for followers included 1. (models.py) create the database elements 2. (test.py) create tests 3. (routes.py) create the view functions 4. Add elements into the html

Something important related to processing of web forms. After I process the form data, I end the request by issuing a redirect to the home page even though this is the view function of the home page. It is a standard practice to respond to a POST request generated by a web form submission with a redirect. Called Post/Redirect/Get pattern

start at password reset tokens