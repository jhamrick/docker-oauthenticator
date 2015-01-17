import json
import socket

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.netutil import Resolver

from jupyterhub.auth import LocalAuthenticator
from oauthenticator import GitHubOAuthenticator
from dockerspawner.systemuserspawner import SystemUserSpawner


class UnixResolver(Resolver):
    """UnixResolver from https://gist.github.com/bdarnell/8641880"""
    def initialize(self, resolver, socket_path):
        self.resolver = resolver
        self.socket_path = socket_path

    def close(self):
        self.resolver.close()

    @gen.coroutine
    def resolve(self, host, port, *args, **kwargs):
        if host == 'unix+restuser':
            raise gen.Return([(socket.AF_UNIX, self.socket_path)])
        result = yield self.resolver.resolve(host, port, *args, **kwargs)
        raise gen.Return(result)


class DockerAuthenticator(LocalAuthenticator):
    """A version that performs local system user creation from within a
    docker container.

    """

    resolver = UnixResolver(resolver=Resolver(), socket_path='/restuser.sock')
    AsyncHTTPClient.configure(None, resolver=resolver)
    client = AsyncHTTPClient()
    
    def system_user_exists(self, user):
        # user_id is stored in state after looking it up
        return user.state and 'user_id' in user.state
    
    @gen.coroutine
    def add_system_user(self, user):
        """Add a new user.

        This adds the user to the whitelist, and creates a system user by
        accessing a simple REST api.

        """
        try:
            resp = yield self.client.fetch('http://unix+restuser/' + user.name, method='POST', body='{}')
        except HTTPError as e:
            self.log.error("Failed to create %r", user.name, exc_info=True)
            raise

        # todo: save the user id into the whitelist or somewhere
        info = json.loads(resp.body.decode('utf8', 'replace'))
        self.log.info("Created user %s with uid %i", user.name, info['uid'])
        if user.state is None:
            user.state = {}
        user.state['user_id'] = info['uid']
        self.db.commit()


class DockerOAuthenticator(DockerAuthenticator, GitHubOAuthenticator):
    """A version that mixes in local system user creation from within a
    docker container, and GitHub OAuthentication.

    """
    pass


class SystemUserDockerSpawner(SystemUserSpawner):
    """SystemDockerSpawner that stores user_id in spawner state"""
    def load_state(self, state):
        super().load_state(state)
        self.user_ids[self.user.name] = state['user_id']
    
    def get_state(self):
        state = super().get_state()
        state['user_id'] = self.user_ids[self.user.name]
        return state
