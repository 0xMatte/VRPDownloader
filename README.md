VRP Game Downloader
===================

VRPirates wrapper to download game files without using the bloated [Rookie](https://github.com/VRPirates/rookie)

Requirements
------------

```sh
pip install requests
apt install p7zip-full
apt install rclone
```

Usage
-----
Search using the game name, download it using the number, you can also search for numbers using the _+_

e.g.
```
$ ./vrpirates.py
[+] Binaries satisfacted
[+] Config fetched
[+] Gamelist updated

Search game by name, use index to select
> beat saber
 104  Beat Saber | 2023-12-13 21:50 UTC | 4134MB
 ...
 108  Beat Saber w.BMBF | 2023-05-25 11:16 UTC | 3431MB
> +2021
 931  Santa's Reindeer Racing 2021 | 2023-08-22 12:45 UTC | 191MB
> 104

[+] Downloading...
...
```

## Manual procedure

### Get url / password
```
curl -k https://wiki.vrpirates.club/downloads/vrp-public.json
```
```json
{
  "baseUri":"https://theapp.vrrookie.xyz/",
  "password":"🤭"
}
```

### Download game list
```sh
rclone sync ":http:/meta.7z" . --http-url https://theapp.vrrookie.xyz/ --tpslimit 1.0 --tpslimit-burst 3 --user-agent "rclone/v1.60.1"
```

### Extract meta.7z
Use the base64 decoded password
```sh
7z e -y meta.7z -p🤭 VRP-GameList.txt
```

### Get game hash
Use _Release Name_ column and md5sum with _newline_
```sh
echo "Beat Saber v1011+1.34.2_7115288407 -VRP" | md5sum
```

### Download the game
```sh
rclone copy ":http:/523d5c0905acb71ea164029f2017bac8/" . --transfers 1 --multi-thread-streams 0 --progress --rc --http-url https://theapp.vrrookie.xyz/ --tpslimit 1.0 --tpslimit-burst 3 --user-agent "rclone/v1.60.1"
```

### Extract the game
Same as the _meta.7z_ file, in case of multiple volume it's all automatic
```sh
7z x -p🤭 523d5c0905acb71ea164029f2017bac8.7z.001
```

### Sideload the apk / obb
Install the _apk_
```sh
adb install -g -r com.beatgames.beatsaber.apk
```
Create destination folder (fix for Q3)
```sh
adb shell mkdir /sdcard/Android/obb/com.beatgames.beatsaber
```
Push the _obb_ files
```sh
adb push com.beatgames.beatsaber/* /sdcard/Android/obb/com.beatgames.beatsaber
```
