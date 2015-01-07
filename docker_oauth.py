import json
import socket

from tornado import gen
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.netutil import Resolver

from oauthenticator import LocalGitHubOAuthenticator


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


class DockerOAuthenticator(LocalGitHubOAuthenticator):
    """A version that mixes in local system user creation, but does so
    from within a docker container

    """

    resolver = UnixResolver(resolver=Resolver(), socket_pack='/var/run/restuser/restuser.sock')
    AsyncHTTPClient.configure(None, resolver=resolver)
    client = AsyncHTTPClient()

    @gen.coroutine
    def add_user(self, user):
        """Add a new user.

        This adds the user to the whitelist, and creates a system user by
        accessing a simple REST api.

        """

        try:
            resp = yield self.client.fetch('http://unix+restuser/' + user, method='POST', body='{}')
        except HTTPError as e:
            print(e.response.code, e.response.body.decode('utf8', 'replace'))
            return

        # todo: save the user id into the whitelist or somewhere
        user = json.loads(resp.body.decode('utf8', 'replace'))
        self.log.debug(user)
