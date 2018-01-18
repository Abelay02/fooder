Design Document

1. A "design document" for your project in the form of a Markdown file called DESIGN.md that discusses, technically,
how you implemented your project and why you made the design decisions you did. Your design document should be at
least several paragraphs in length. Whereas your documentation is meant to be a user’s manual, consider your design
document your opportunity to give the staff a technical tour of your project underneath its hood.


Our project was an app that allowed individuals to see what other Harvard students in their
vicinity were purchasing and contact them to be able to opt into their with them. The app
in effect widens the effective social circle of individuals who wish to purchase goods such
that they can receive reap the benefits of buying in bulk. This project was no small task we
have several design and implementation question and ultimately we reached the project that we have today.

The backbone of our project is our database. The structuring our database in an efficient way
was crucial to the completion of project. Along the way, in order to increase the security and
functionality of our website we added several columns to our original users table. We have the
standard user password etc, but it was here than we set the stage for a feature that would make
the website far more secure for Harvard students, email verification. We also implemented a rating
system to encourage positive interactions. For the email verification we had to download an extension
called flask mail (sourced from mail.smtp2go.com) and generate a random code, which we did by importing
random into python. The value is generated every time a user registers and is sent to the users email
address, which we declared must be a Harvard address. We then mandated that the confirmation code had
to be input before accessing any webpage. Thus we had email verification such that no user could join without a Harvard email address.
The login and register feature were fairly standard aside from that.

We then implemented an index page using SQL commands in python that would generate a filtered list
of the orders that had been placed through add entry. We used unicode standard time and did calculations
such that no order over two hours old would be visible via the index page. Our reasoning was that for food
two hours was an eternity and the desire to eat or to share with another individual would have forcibly waned.
On the index page we allow individuals to commit to an order using a button. When the button that button is clicked
individuals are add to the commits database and they can no longer commit to the order and are take to the commits page.

We faced several technical issues during the project. The few we were unable to solve in over project were
in regards to dynamic CSS. We originally planned to have contacts as a drop down menu and in fact implemented a
drop down menu, which was rather nice by the way, and we also implemented a star based rating display feature.
However, the problem we faced was that CSS was unable to dynamically display variables in order to create a
table thus we had to get rid of those features because although they looked nice the lack of dynamism made
them effectively useless, and we opted for simpler methods of displaying the information. This describes the
major details of our app and significant design considerations. We used SQLite as a database and interacted
with it through Python commands and in SQLite we created a view table. So we could save memory, but have
an easier time with SQL commands.

