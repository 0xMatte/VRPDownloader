pRookie minimal VRPirates apk downloader
===================

Like [Rookie](https://github.com/VRPirates/rookie) but minimal for Linux, written in Python.\
discord: `mattewastaken`

Requirements
------------

```sh
pip3 install requests
apt install p7zip-full
apt install rclone
```

Usage
-----
Search using the game name, download it using the number, you can also search for numbers using the _+_

e.g.
```
$ ./prookie.py
[+] Binaries satisfacted
[+] Config fetched
[+] Gamelist updated

Search game by name, use index to select
> beat saber
 110  Beat Saber | 2024-04-11 18:05 UTC | 3875MB
 ...
 114  Beat Saber v1.35.0 | 2024-04-16 05:02 UTC | 3494MB
> +2021
 1044 Santa's Reindeer Racing 2021 | 2023-08-25 19:38 UTC | 191MB
> 110

[+] Downloading...
...
```

## Manual procedure

### Get url / password
```
curl -k https://vrpirates.wiki/downloads/vrp-public.json
```
```json
{
  "baseUri":"https://theapp.vrrookie.xyz/",
  "password":"🤭"
}
```

### Download game list
```sh
rclone sync ":http:/meta.7z" . --http-url https://theapp.vrrookie.xyz/ --tpslimit 1.0 --tpslimit-burst 3 --user-agent "rclone/v1.66.0"
```

### Extract meta.7z
Use the _base64_ decoded password
```sh
7z e -y meta.7z -p$(echo 🤭 | base64 -d) VRP-GameList.txt
```

### Get game hash
Use _Release Name_ column and **md5sum** with _newline_
```sh
echo 'Beat Saber v1188+1.36.0_8486341502 -VRP' | md5sum
```

### Download the game
```sh
rclone copy ":http:/295e02d0861558814c38fdb3b1ab2f7a/" . --transfers 1 --multi-thread-streams 0 --progress --rc --http-url https://theapp.vrrookie.xyz/ --tpslimit 1.0 --tpslimit-burst 3 --user-agent "rclone/v1.66.0"
```

### Extract the game
Same as the _meta.7z_ file, in case of multiple volume it's all automatic
```sh
7z x -p$(echo 🤭 | base64 -d) 295e02d0861558814c38fdb3b1ab2f7a.7z.001
```

### Sideload the apk & obb
Install the _apk_
```sh
adb install -r com.beatgames.beatsaber.apk
```
Create destination folder (fix for Q3)
```sh
adb shell mkdir /sdcard/Android/obb/com.beatgames.beatsaber
```
Push the _obb_ files
```sh
adb push com.beatgames.beatsaber/* /sdcard/Android/obb/com.beatgames.beatsaber
```
