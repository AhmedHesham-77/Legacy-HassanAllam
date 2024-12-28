# Fida

This repo we solved problem faced us that in GEM it has Fida commercial Displays that in ICT department we need to be updated with its state minute by minute so if is there any problem in any of them we solve it immediately.

**Backend**<br>
According to the problem i create automated script that read status data from display every minute, Display working with SNMP protocol so i create two methods one to get data and one to set data according to that theres data has to be updated if needed like time of working display an brightness and so on, Then data gained stored in sqlite database and updated if theres updates, Then use database to create API for this data with Fast Api and finally to make this code updated use schedules.

**Frontend**<br>
After finishing the backend, I used flutter to create a simple UI to display the data and update its state if it has a new value by reading the generated API and using the riverpod framework to call and track changes in the API and if any changes are made, update the state of the data variables which will be updated across all pages of the app.
