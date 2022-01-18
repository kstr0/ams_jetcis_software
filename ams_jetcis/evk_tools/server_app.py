__author__ = "Denver Lloyd"
__copyright__ = "Copyright 2021, AMS Characterization"


import paramiko
import numpy as np
import os
import subprocess as sp
import pdb
import sys
import pandas as pd

class Server_App:
    def __init__(self,
                 username='jetcis',
                 password='jetcis',
                 port=22,
                 hostname='192.168.1.35',
                 hpath=r'/home/jetcis/staged_images',
                 rpath=r'C:\data\trans',
                 sensor_name='Mira050',
                 capture_script=r'/home/jetcis/jetcis/software/trunk/sw/ams_jetcis/evk_tools/server_app_host.py',
                 config_path_host=r'/home/jetcis/jetcis/software/trunk/sw/ams_jetcis/configs/Mira050.ini',
                 config_path_rec=None):
        """
        Class for remotely capturing and sending data from the EVK to receiving
        machine

        TODO: provide usage link

        Keyword Arguments:
            username (str): username to access host
            password (str): password to access host
            port (int): port to use for accessing ssh
            hostname (str): IP address of host machine
            hpath (str): path on host machine to use for saving images
                         Note: this is only a staging folder prior to 
                               transfer to the receiver
            rpath (str): local path where images from host should be saved
            capture script (str): path to capture script on host
                                  Note: `server_app_host.py` must be the
                                        capture script
            config_path_host (str): path to config on host machine to be used
                                    for setting sensor state
            config_path_rec (str): config path on receiving machine to be used
                                   for setting the sensor state
                                   Note: If this param is used this config
                                         will be sent to the host and used
                                         to set the sensor state

        """

        # instance variables
        self.username = username
        self.password = password
        self.port = port
        self.hostname = hostname
        self.rpath = rpath
        self.hpath = hpath
        self.fname = ''
        self.full_path = ''
        self.sm = object
        self.host_dir_ims = []
        self.valid_dir = False
        self.capture_script = capture_script
        self.config_path_host = config_path_host
        self.config_path_rec = config_path_rec
        self.sensor_name = sensor_name
        self.raw = pd.DataFrame()
        self.host_dir_ims = []

        # connect to ssh to deploy imaging script
        self.ssh_connect()

    def main(self, label=None):
        """
        The sequence ran below will capture, send, and
        save images on the receiver

        Keyword Arguments:
            label (str): label to be added to images on receiver
                         machine
        """

        # case 1 where we want to transfer a config of receiver
        # to be used on host machine
        if not isinstance(self.config_path_rec, type(None)):

            # write config to host machine
            self.transfer_config()

        # capture images on evk
        self.get_images()

        # transfer to receiver pc
        self.transfer()

        # rename images if label is not None
        if not isinstance(label, type(None)):
            self.rename_stack(label)

        # delete images from host machine
        self.delete_images()

    def transfer_config(self):
        """
        Transfers the config from the receiver machine to the
        host machine to be used to set the sensor state if
        keyword `config_path_rec` is used
        """

        # make sure config path on receiver exists
        if not os.path.exists(self.config_path_rec):
            print(f'config path not found on receiver pc!\
                  Check path {self.config_path_rec}')
            sys.exit()

        # get path config should be sent to on host
        base = os.path.dirname(self.config_path_host)
        fname = os.path.basename(self.config_path_rec)
        write_path = base + '/' + fname

        # write to config to host
        cmd = f'pscp -pw {self.password} {self.config_path_rec} {self.username}@{self.hostname}:{write_path}'
        sp.call(cmd)

        # update config path before running image capture
        self.config_path_host = write_path

        return self

    def transfer(self):
        """
        transfers data from host machine to receiver
        once capture has occured on the host
        """

        # get contents of host dir for transfer
        # path to state DataFrame on host machine
        raw_path = self.hpath + '/' + 'RAW.csv'

        # command line to transfer from host to receiver
        cmd = f'pscp -pw {self.password} {self.username}@{self.hostname}:{raw_path} {self.rpath}'

        # run the command to transfer state file
        sp.call(cmd)

        # read in state DataFrame
        read_path = os.path.join(self.rpath, 'RAW.csv')
        self.raw = pd.read_csv(read_path)

        # get list of image paths
        self.host_dir_ims = self.raw['image_path'].unique()

        # remove .csv so we only have image data
        self.host_dir_ims = [im for im in self.host_dir_ims if '.csv' not in im]

        # transfer images
        for name in self.host_dir_ims:

            # command line to transfer from host to receiver
            cmd = f'pscp -pw {self.password} {self.username}@{self.hostname}:{name} {self.rpath}'

            # run the command
            sp.call(cmd)

        return self

    def ssh_connect(self):
        """
        Connect to the host over ssh
        """

        msg = 'Connected to paramiko (ssh)'

        try:
            # connect to the client
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(hostname=self.hostname,
                                port=self.port,
                                username=self.username,
                                password=self.password)
        except Exception as e:
            msg = f'Connection Failed, Error: {e}'

        print(msg)

        return self

    def get_images(self):
        """
        Runs `server_app_host.py` on host machine

        Returns:
            std_out (str): anything printed to the evk consol upon
                           running the capture script

        """
        params = f'-sn {self.sensor_name}\
                  -cp {self.config_path_host}\
                  -hp {self.hpath}'

        std_out = self.run_command_script(script=self.capture_script,
                                          params=params)

        return std_out

    def delete_images(self):
        """
        Deletes images from host machine before next capture
        """

        params = f'cd {self.hpath}; rm *.tiff'

        std_out = self.run_command_script(script='',
                                          params=params,
                                          python=False)

        return std_out

    def run_command_script(self, script, params, python=True):
        """
        generically run a script or command on the host machine.
        This is equivalent of running a script directly from command line, ex:
        'python3 my_script.py arg1 arg2 arg_n'
        or if python=False:
        'arg1 arg2 arg_n`

        Keyword Arguments:
            script (str): path to script to be ran on host machine
            params (str): list of params required to execute script
                          in the following format:
                          params='arg1 arg2 arg3'

        Returns:
            out1 (list): list of everything printed by stdout during
                         execution of the script on the host machine
        """

        out1 = []

        # check if a python script is being ran
        if python:
            cmd = f'python3 {script} {params}'
        else:
            cmd = f'{params}'

        # run the script on the host machine console
        stdin, stdout, stderr = \
            self.client.exec_command(cmd,
                                     get_pty=True)

        # grab everything from stdout on host machine
        while not stdout.channel.exit_status_ready():
            out = stdout.channel.recv(1024)
            out1.append(out)

        return out1

    def rename_stack(self, save_str):
        """
        Ranmes the stack of images transferred from the host
        machine based on save_str input and updates the state
        file to reflect new image paths

        Keyword Arguments:
            save_str (str): Label string to be added to image path names
        """

        # iterate over images
        for mm in self.host_dir_ims:

            fname = os.path.basename(mm)

            # update save string to include fno
            save_str_ = save_str + '_' + fname

            # get old path
            old_path = os.path.join(self.rpath, fname)

            # get new path
            path = os.path.join(self.rpath, save_str_)

            # rename
            if os.path.exists(path):
                os.remove(path)

            os.rename(old_path, path)

            # update csv
            self.raw.loc[self.raw['image_path'] == mm, 'image_path'] = path

        # save updated csv
        self.raw.to_csv(os.path.join(self.rpath, 'RAW.csv'), index=False)

        return self
