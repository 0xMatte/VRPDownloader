#!/usr/bin/env python3
from base64 import b64decode
from hashlib import md5
import subprocess
import requests
import csv
import os

# Disable SSL warnings
requests.packages.urllib3.disable_warnings()

class pRookie:
    def __init__(self,
            config_link: str, data_directory: str = 'data',
            rclone_user_agent: str = 'rclone/v1.66.0'
        ) -> None:

        # Ensure the presence of rclone/7z
        self._assert_bins()
        # Create dirs
        self._assert_dirs(data_directory)

        self.data_directory = data_directory
        self.rclone_user_agent = rclone_user_agent
        self._game_list_filename = 'VRP-GameList.txt'
        self._game_list = None
        self._game_hash = None

        # Load game list
        self._fetch_config(config_link)
        self.update_game_list()

    def _assert_bins(self) -> None:
        try:
            subprocess.run(
                ['rclone', 'version'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except FileNotFoundError:
            raise FileNotFoundError('RCLONE not installed!')

        try:
            subprocess.run(
                ['7z'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except FileNotFoundError:
            raise FileNotFoundError('7z not installed!')

        print('[+] Binaries satisfacted')

    def _assert_dirs(self, root: str) -> None:
        os.makedirs(root, exist_ok=True)

    def _fetch_config(self, url: str) -> None:
        try:
            r = requests.get(url, timeout=10, allow_redirects=False, verify=False)
            assert r.ok
        except:
            raise ValueError('Error while fetching config link!')

        config: dict = r.json()

        if ('baseUri' not in config) or ('password' not in config):
            raise KeyError('Missing key in config json!')

        try:    config['password'] = b64decode(config['password']).decode()
        except: pass

        self._config_uri = config.get('baseUri')
        self._config_password = config.get('password')

        print('[+] Config fetched')

    def _set_hash_from_releasename(self, name: str) -> str:
        game_hash = md5((name + '\n').encode()).hexdigest()
        self._game_hash = game_hash
        return game_hash

    def update_game_list(self) -> None:
        filename = 'meta.7z'

        # Download meta.7z
        rclone_sync_command = [
            'rclone', 'sync', ':http:/' + filename, self.data_directory,
            '--http-url', self._config_uri, '--tpslimit', '1.0',
            '--tpslimit-burst', '3', '--user-agent', self.rclone_user_agent
        ]

        try:
            subprocess.run(
                rclone_sync_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f'Error downloading {filename} with rclone!')

        # Extract gamelist
        extract_command = [
            '7z', 'e', '-y', filename,
            '-p' + self._config_password, self._game_list_filename
        ]

        try:
            subprocess.run(
                extract_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=self.data_directory,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f'Error while extracting {filename} with 7z!')

        # Load gamelist
        game_list_path = os.path.join(self.data_directory, self._game_list_filename)

        if not os.path.isfile(game_list_path):
            raise FileNotFoundError('Missing game list: ' + game_list_path)

        with open(game_list_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')

            _ = next(reader)
            # Game name | Release Name | Last Updated | Size
            games = [(x[0], x[1], x[4], x[5]) for x in reader]

        self._game_list = games

        print('[+] Gamelist updated')

    def list_game_by_name(self, game_name: str) -> None:
        for i, (name, _, update, size) in enumerate(self._game_list):
            if game_name.lower() in name.lower():
                print(f' {i:<4} {name} | {update} | {size}MB')

    def search_game(self) -> str:
        print('\nSearch game by name, use index to select')

        while True:
            user_input = input('> ')

            if user_input.isnumeric() and int(user_input) < len(self._game_list):
                choice = int(user_input)
                break

            self.list_game_by_name(user_input.lstrip('+'))

        game_release_name = self._game_list[choice][1]
        return self._set_hash_from_releasename(game_release_name)

    def download_game(self, game_hash: str = None) -> None:
        if game_hash:
            self._game_hash = game_hash

        if not self._game_hash:
            self.search_game()

        # Download the selected game
        print('\n[+] Downloading...\n')
        rclone_copy_command = [
            'rclone', 'copy', f':http:/{self._game_hash}/', self.data_directory,
            '--transfers', '1', '--multi-thread-streams', '0',
            '--progress', '--rc', '--http-url', self._config_uri,
            '--tpslimit', '1.0', '--tpslimit-burst', '3',
            '--user-agent', self.rclone_user_agent
        ]

        try:
            subprocess.run(
                rclone_copy_command,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f'Error downloading {self._game_hash} with rclone!')

        # Extract the game
        game_path = os.path.join(self.data_directory, self._game_hash + '.7z.001')
        extract_command = [
            '7z', 'x', '-y', '-p' + self._config_password,
            game_path
        ]

        print('\n[+] Download complete, extracting...')
        try:
            subprocess.run(
                extract_command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f'Error while extracting {game_path}.7z.001')

        # Clean downloaded 7z
        for file in os.listdir(self.data_directory):
            if file.startswith(self._game_hash):
                os.remove(os.path.join(self.data_directory, file))
        self._game_hash = None

        print('[+] Game successfully downloaded and extracted!')


if __name__ == '__main__':
    downloader = pRookie(config_link='https://vrpirates.wiki/downloads/vrp-public.json')
    downloader.download_game()
