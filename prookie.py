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
    def __init__(self, config_link: str, root_directory: str = 'config') -> None:
        # Ensure the presence of rclone/7z
        self._assert_bins()
        # Create dirs
        self._assert_dirs(root_directory)

        # Set file directory
        self.root_directory = root_directory

        # Fetch new config
        config = self._fetch_config(config_link)

        # Setup config values
        self._config_uri = config.get('baseUri')
        self._config_password = config.get('password')

        # Game list filename
        self._game_list_filename = 'VRP-GameList.txt'
        self._game_list = None

        # Game to download
        self._game_hash = None

    def _assert_bins(self) -> None:
        rclone = 'rclone version'
        result = subprocess.getoutput(rclone)
        assert 'rclone' in result and 'not found' not in result, 'RCLONE not installed!'

        sevenZip = '7z'
        result = subprocess.getoutput(sevenZip)
        assert '7-Zip' in result, '7z not installed!'

        print('[+] Binaries satisfacted')

    def _assert_dirs(self, root: str) -> None:
        os.makedirs(root, exist_ok=True)

    def _fetch_config(self, url: str) -> dict:
        try:
            r = requests.get(url, timeout=10, allow_redirects=False, verify=False)
            assert r.ok
        except:
            raise ValueError('Error while fetching config link!')

        config = r.json()

        if ('baseUri' not in config) or ('password' not in config):
            raise KeyError('Missing key in config json!')

        try:    config['password'] = b64decode(config['password']).decode()
        except: pass

        print('[+] Config fetched')
        return config

    def _load_game_list(self) -> None:
        game_list_path = os.path.join(self.root_directory, self._game_list_filename)

        if not os.path.isfile(game_list_path):
            raise FileNotFoundError('Missing game list: ' + game_list_path)

        with open(game_list_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f, delimiter=';')

            _ = next(reader)
            # Game name | Release Name | Last Updated | Size
            games = [(x[0], x[1], x[4], x[5]) for x in reader]

        self._game_list = games

    def update_game_list(self) -> None:
        filename = 'meta.7z'

        # Download meta.7z
        rclone_sync_command = [
            'rclone', 'sync', ':http:/' + filename, self.root_directory,
            '--http-url', self._config_uri, '--tpslimit', '1.0',
            '--tpslimit-burst', '3', '--user-agent', 'rclone/v1.66.0'
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
                cwd=self.root_directory,
                check=True
            )
        except subprocess.CalledProcessError:
            raise RuntimeError(f'Error while extracting {filename} with 7z!')

        print('[+] Gamelist updated')

    def list_game_by_name(self, game_name: str) -> None:
        if not self._game_list:
            self._load_game_list()

        for i, (name, _, update, size) in enumerate(self._game_list):
            if game_name.lower() in name.lower():
                print(f' {i:<4} {name} | {update} | {size}MB')

    def search_game(self) -> str:
        if not self._game_list:
            self._load_game_list()

        print('\nSearch game by name, use index to select')
        while True:
            user_input = input('> ')

            if user_input.isnumeric() and int(user_input) < len(self._game_list):
                choice = int(user_input)
                break

            self.list_game_by_name(user_input.lstrip('+'))

        game_release_name = self._game_list[choice][1] + '\n'
        game_hash = md5(game_release_name.encode()).hexdigest()

        self._game_hash = game_hash

        return game_hash

    def download_game(self, game_hash: str = None) -> None:
        if game_hash:
            self._game_hash = game_hash

        if not self._game_hash:
            self.search_game()

        # Download the selected game
        print('\n[+] Downloading...\n')
        rclone_copy_command = [
            'rclone', 'copy', f':http:/{self._game_hash}/', self.root_directory,
            '--transfers', '1', '--multi-thread-streams', '0',
            '--progress', '--rc', '--http-url', self._config_uri,
            '--tpslimit', '1.0', '--tpslimit-burst', '3',
            '--user-agent', 'rclone/v1.66.0'
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
        game_path = os.path.join(self.root_directory, self._game_hash + '.7z.001')
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

        print('[+] Game successfully downloaded and extracted!')


if __name__ == '__main__':
    downloader = pRookie(config_link='https://vrpirates.wiki/downloads/vrp-public.json')

    downloader.update_game_list()
    downloader.search_game()
    downloader.download_game()
