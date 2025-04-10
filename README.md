# Order Generator

## Function
This application is the main backend AI scheduler for order management At MADE CC

## Default Port
`3070`

## Environment Variables
The application requires the following environment variables:

- `ORION_LD_URL` (default: `localhost`)
- `ORION_LD_PORT` (default: `1026`)
- `CONTEXT_HOST` (default: `localhost`)
- `CONTEXT_PORT` (default: `5051`)
- `ORION_LD_URL_POLIMI` (default: <Orion_machine_IP>)
- `ORION_LD_PORT_POLIMI` (default: `31550`)
- `CONTEXT_HOST_POLIMI` (default: `context.default.svc.cluster.local`)
- `CONTEXT_PORT_POLIMI` (default: `5051`)
## Application Screenshot
![screenshot](App_Screenshot.png)

## Usage
To start, pull the repo from GitHub and run the following commands:

```sh
$ py -m venv .venv
$ pip install -r requirements.txt
$ py app.py
```
## Running from docker images
Use following command with the necessary changes to the environment variables as per actual deployment scenario

```sh
$ docker run -p 3070:3070 -e ORION_LD_HOST=<host> -e ORION_LD_PORT=<port> -e CONTEXT_HOST=<host> -e CONTEXT_PORT=<port> -e ORION_LD_HOST_POLIMI=<host> -e ORION_LD_PORT_POLIMI=<port> -e CONTEXT_HOST_POLIMI=<host> -e CONTEXT_PORT_POLIMI=<port> danny0117/aeros-rag:<image_tag>
```