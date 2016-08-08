import os
import txaio
txaio.use_twisted()
from autobahn.wamp import cryptosign

#from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.twisted.wamp import ApplicationSession, ApplicationRunner


class MyComponent(ApplicationSession):

    def onConnect(self):
        self.log.info("connected to router")

        # authentication extra information for wamp-cryptosign
        #
        extra = {
            # forward the client pubkey: this allows us to omit authid as
            # the router can identify us with the pubkey already
            u'pubkey': self.config.extra[u'key'].public_key(),

            # not yet implemented. a public key the router should provide
            # a trustchain for it's public key. the trustroot can eg be
            # hard-coded in the client, or come from a command line option.
            u'trustroot': None,

            # not yet implemented. for authenticating the router, this
            # challenge will need to be signed by the router and send back
            # in AUTHENTICATE for client to verify. A string with a hex
            # encoded 32 bytes random value.
            u'challenge': None,

            u'channel_binding': u'tls-unique'
        }

        # now request to join ..
        self.join(self.config.realm,
                  authmethods=[u'cryptosign'],
                  authextra=extra)

    def onChallenge(self, challenge):
        self.log.info("authentication challenge received: {challenge}", challenge=challenge)
        # alright, we've got a challenge from the router.

        # not yet implemented. check the trustchain the router provided against
        # our trustroot, and check the signature provided by the
        # router for our previous challenge. if both are ok, everything
        # is fine - the router is authentic wrt our trustroot.

        # sign the challenge with our private key.
        signed_challenge = self.config.extra[u'key'].sign_challenge(self, challenge)

        # send back the signed challenge for verification
        return signed_challenge

    def onJoin(self, details):
        self.log.info("session joined: {details}", details=details)
        self.log.info("*** Hooray! We've been successfully authenticated with WAMP-cryptosign using Ed25519! ***")
        self.leave()

    def onLeave(self, details):
        self.log.info("session closed: {details}", details=details)
        self.disconnect()

    def onDisconnect(self):
        self.log.info("connection to router closed")


if __name__ == '__main__':

    fn = os.path.join(os.path.expanduser('~'), '.ssh', 'id_ed25519')
    fn = 'oberstet'

    key = cryptosign.SigningKey.from_ssh_key(fn)
    extra = {
        u'key': key
    }

    runner = ApplicationRunner(
        u'ws://127.0.0.1:8080/ws',
        u'com.crossbario.cdc.mrealm-test1',
        extra=extra
    )
    runner.run(MyComponent)