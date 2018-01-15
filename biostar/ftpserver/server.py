import os


from pyftpdlib.servers import FTPServer
from biostar.ftpserver.handler import BiostarFTPHandler, BiostarAuthorizer, BiostarFileSystem
from biostar.accounts import models
import logging



def start():
    # Engine authorization comes from the accounts.
    authorizer = BiostarAuthorizer()

    # This is a test user. Will be removed.
    for user in models.User.objects.all():

        # TODO:user.password is salted hash string so can't add users from biostar.accounts this way
        #authorizer.add_user(user.email, user.password, user=user, perm='elradfmwMT')
        print (user, user.email)

    user = models.User.objects.filter(email="1@lvh.me").first()

    # TODO: saves password as plain-text---no bueno
    authorizer.add_user("1@lvh.me","1@lvh.me" , user=user, perm='elradfmwMT')

    # When parameter user is not specified; we user AnonymousUser
    authorizer.add_user('user', '12345', perm='elradfmwMT')
    authorizer.add_user('user2', '12345', perm='elradfmwMT')

    # Instantiate FTP handler class.
    handler = BiostarFTPHandler
    handler.authorizer = authorizer

    handler.abstracted_fs = BiostarFileSystem

    # Define a customized banner (string returned when client connects)
    handler.banner = "Welcome to Biostar-Engine"

    # Listen on 0.0.0.0:8021
    address = ('lvh.me', 8021)
    server = FTPServer(address, handler)

    # FTP connection settings.
    server.max_cons = 256
    server.max_cons_per_ip = 5

    # Start ftp server.
    server.serve_forever()



