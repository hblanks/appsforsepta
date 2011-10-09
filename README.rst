============
appsforsepta
============

This provides a couple more API's for the Apps for Septa Hackathon,
with deployment to EC2. Of note are:

    - JSONP for bus locations, e.g.:

        /app/transitview/bus_route_data/42?callback=f

    - JSON/JSONP interface to the Septa trip planner, e.g.:

        /app/tripplanner/?from=4500%20osage%20ave%20philadelphia,%20pa&to=broad%20and%20south

To instantiate, do:

    ./deployment/instantiator.py --user-data ./deployment/user_data.sh launch

after creating a security group.


TODO:

    - add the Bryan's iOS source code

    - finish adding in Mike's HTML code

    - create the security group on boot

    - find hosting!