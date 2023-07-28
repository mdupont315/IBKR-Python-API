Purpose
===
A simple trading equity trading model on Interactive Brokers' API dealing with (pseudo) high-frequency data studies.

Requirements
===

- Python 3.7
- IB Trader Workstation Build 973.2
- IB paper or live trading account    

Setting up
===

## Running on a local Python console 

Steps to run the trading model on your command line:

- Within a Python 3.7 environment, install the requirements:
    
        pip install -r requirements.txt

- In IB Trader Workstation (TWS), go to **Configuration** > **Api** > **Settings** and:

    - enable ActiveX and Socket Clients
    - check the port number you will be using
    - If using Docker, uncheck **Allow connections from localhost only** and enter the machine IP running this model to **Trusted IPs**.

- Update `main.py` with the required parameters and run the model with the command:

        python main.py
    
## Running from a Docker container

This step is optional. You can choose to deploy one or several instances of these algos on a remote machine for execution using Docker.

A Docker container helps to automatically build your running environment and isolate changes, all in just a few simple commands!

To run this trading model in headless mode:

- In TWS, ensure that remote API connections are accepted and the Docker machine's IP is added to **Trusted IPs**.

- Ensure your machine has docker and docker-compose installed. Build the image with this command:

        docker-compose build
        
- Update the parameters in `docker-compose.yml`. I've set the `TWS_HOST` value in my environment variables. This is the IP address of the remote machine running TWS. Or, you can just manually enter the IP address value directly. Then, run the image as a container instance:

        docker-compose up
        
    To run in headless mode, simply add the detached command `-d`, like this:
    
        docker-compose up -d
        
    In headless mode, you would have to start and stop the containers manually.

