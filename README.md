Custom OAuthenticator + DockerSpawner 

To build the image, add userlist of the form:

    username
    username admin
    username
    ...

And build:

    docker build -t jupyterhub-system-docker

Add your GitHub credentials to an `env` file:

    GITHUB_CLIENT_ID=[something]
    GITHUB_CLIENT_SECRET=[something-else]
    OAUTH_CALLBACK_URL=http://[HOST]/hub/oauth_callback
    JPY_COOKIE_SECRET=[abc123]

Start the [restuser](https://github.com/minrk/restuser) service on the host:

    python /path/to/restuser.py --socket=/var/run/restuser.sock

And run JupyterHub:

    docker run --net=host --env-file=env -v /var/run/docker.sock:/docker.sock -v /var/run/restuser.sock:/restuser.sock -it hub

It will create real unix users on the host system on demand
and start single-user docker containers,
mounting each user's home directory.
