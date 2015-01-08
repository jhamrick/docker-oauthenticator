FROM jhamrick/jupyterhub

ADD docker_oauth.py /srv/oauthenticator/docker_oauth.py

# override ONBUILD ADD while we work on the hub config
ADD jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
