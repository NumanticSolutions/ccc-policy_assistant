# © 2025 Numantic Solutions LLC
# MIT License
#
#

import os
import json

# Environment variables for API credential storage
# import dotenv
from dotenv import dotenv_values
from dotenv import load_dotenv

from google.cloud import secretmanager

import warnings




class ApiAuthentication:
    '''
    Class to store API authentication credentials in an object.

    Attributes

        dotenv_path: Path to .env file used by dotenv
        cred_source: Credential source:
            'local': Credentials come from a local .env file

    '''

    def __init__(self,
                 client: str,
                 **kwargs):
        '''
        Initialize class

        '''

        self.dotenv_path = "{}/.numantic/keys/{}".format(os.environ["HOME"],
                                                        client)
        self.override = True
        self.cred_source = "dotenv"

        # Update any key word args
        self.__dict__.update(kwargs)

        # Set up error message
        self.error_message = None

        # Get the database configuration
        self.__get_api_creds__()

        # Set environment variables - unless it has some error message
        if self.error_message == None:
            self.set_environ_variables()

    def __get_api_creds__(self):
        '''
        Method to retrieve API credentials

        '''

        self.apis_configs = {}

        # check if dotenv_path - if not return None
        if not os.path.exists(self.dotenv_path):
            msg = "The dotenv_path ({}) path could not be found.".format(self.dotenv_path)
            self.error_message = msg
            return None

        # check if .env in the directory
        if ".env" not in os.listdir(self.dotenv_path):
            msg = "No .env file found in dotenv_path directory: {}.".format(self.dotenv_path)
            self.error_message = msg
            return None

        # Get the dotenv configuration file
        if self.cred_source == "dotenv":
            creds_file = ".env"
            self.apis_configs = dotenv_values(os.path.join(self.dotenv_path,
                                                           creds_file))

    def set_environ_variables(self):
        '''
        Load environmental variables from a .env file
        '''
        load_dotenv(dotenv_path=os.path.join(self.dotenv_path, ".env"), override=self.override)

    def get_google_secret_value(self,
                                secret_path: str):
        '''
        Get the value of a secret from Google secrets.

        :param
            path: path to the Google secret.
            For example, f"projects/{os.environ["GCP_PROJECT_ID"]}/secrets/FASTAPI_API_KEY/versions/latest"
        '''

        warnings.filterwarnings("ignore")

        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_path)

        try:

            data_bytes = response.payload.data
            return data_bytes.decode('utf-8')

        except:

            msg = ("The secret at the following path could not be found. Please investigate. "
                   "Path: {}").format(secret_path)
            self.error_message = msg
            return None




