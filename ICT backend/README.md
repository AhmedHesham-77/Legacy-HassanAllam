# ICT backend

<div>
    <p>
        This task created according we want to create backend contains all working systems in GEM.<br>
        So we divided task into smaller tasks as each task is a one system and use microservice architecture, My task is to build 5 services from them (Fida, Entertainment, app space, Qsys, postgres) and because each one of them has it's own API i use kong API gateway to combine all of them in one API. 
    </p>
</div>

### App space

<p>
    Here i create automated script that read status data from app space api (it's responsible for display contents in all monitors) and data need modification to be suitable and be like other services API because of that we don't use it directly and modify data and build new API for it use Fast APi.
</p>

### Qsys

<p>
    Here i create automated script that read status data from Qsys sound system api and data need modification to be suitable and be like other services API because of that we don't use it directly and modify data and build new API for it use Fast APi.
</p>

### Fida

<p>
    Here i create automated script that read status data from fida displays every minute, Display working with SNMP protocol so i create two methods one to get data and one to set data according to that theres data has to be updated if needed like time of working display an brightness and so on, Then data gained stored in sqlite database and updated if theres updates, Then use database to create API for this data with Fast Api and finally to make this code updated use schedules.
</p>

### Entertainment

<p>
    Here i create automated script that read status data from GEM grand children museum devices only check if there working and on network by ping on them and store status in sqlite database then create API for it using Fast Api.
</p>

### postgres

<p>
    Here the data collected from all services is stored, such as taking a sample of tables in services every hour and storing it in a new table, this part of the code written in the main code of each service, in the main code of Postgres, use all the tables that contain the sample data to store it in the Postgres database daily for future analysis and tracking the activity of the systems.
</p>
