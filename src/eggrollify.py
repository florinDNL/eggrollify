import os
import sys
import time
import psutil
import shutil
import tarfile
import tempfile
import argparse
import requests

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

HOME = os.path.expanduser("~")
TEMP_FOLDER = tempfile.gettempdir()
steamDir = ''

steamDirs = [
    '.steam',
    '.local/share/steam',
    'snap/steam/common/.steam/steam'
    '.var/app/com.valvesoftware.Steam/data/Steam/'
]

for dir in steamDirs:
    if os.path.exists(os.path.join(HOME, dir)):
        steamDir = os.path.join(HOME, dir)

if not os.path.exists(TEMP_FOLDER):
    os.makedirs(TEMP_FOLDER)

if not steamDir:
    print(f'{bcolors.FAIL}Steam directory not found. Is Steam installed?{bcolors.ENDC}')
    exit()

COMPAT_DIR = os.path.join(steamDir, 'steam/compatibilitytools.d')



def getInstalledVersions():
    protonDirs = os.listdir(COMPAT_DIR)
    protonGeDirs = []

    for dir in protonDirs:
        if 'GE-' in dir:
            protonGeDirs.append(dir)

    return protonGeDirs



def isAlreadyInstalled(version):
    installedVersions = getInstalledVersions()
    if version in installedVersions:
        return True    
    return False



def getEggrollReleases():
    URL = 'https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases'
    releases = requests.get(URL).json()
    return releases



def getUserInput(releases):    
    count = 1
    for release in releases:
        print(f"{count}) {release['tag_name']}")
        count += 1
    
    print('\n0) Exit')
    
    selection = int(input('\nSelect version to install: '))
    
    if selection > len(releases):
        print(f'{bcolors.FAIL}Invalid Choice{bcolors.ENDC}')
        exit()
    
    if selection == 0:
        exit()

    return selection



def getDownloadURL(selection, releases):
    tagName = releases[selection - 1]['tag_name']

    if isAlreadyInstalled(tagName):
        print(f"{bcolors.WARNING}Version {tagName} is already installed{bcolors.ENDC}")
        exit()

    assetsURL = releases[selection-1]['assets_url']
    assets = requests.get(assetsURL).json()
    downloadURL = assets[1]['browser_download_url']

    return downloadURL



def download(url: str):
    filename = url.split('/')[-1].replace(" ", "_")
    file_path = os.path.join(TEMP_FOLDER, filename)

    r = requests.get(url, stream=True)
    length = r.headers.get('content-length')

    if r.ok:
        dl = 0
        length = int(length)
        print(f"{bcolors.BOLD}Downloading {filename} to {bcolors.UNDERLINE}{TEMP_FOLDER}{bcolors.ENDC}")        
        with open(file_path, 'wb') as f:        
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    dl += len(chunk)
                    f.write(chunk)
                    f.flush()
                    os.fsync(f.fileno())
                    done = int(50 * dl / length)
                    sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )    
                    sys.stdout.flush()
    else:
        print("Could not download")
        exit()

    return file_path



def cleanTempDir(filepath):
    os.remove(filepath)
    print(f'{bcolors.OKCYAN}Temporary download {bcolors.UNDERLINE}{filepath}{bcolors.ENDC} deleted.{bcolors.ENDC}')



def decompressTarBall(tarball):    
    archive = tarfile.open(tarball)

    print(f'\n{bcolors.BOLD}Extracting {bcolors.UNDERLINE}{tarball}{bcolors.ENDC} build{bcolors.ENDC}')

    archive.extractall(COMPAT_DIR)
    archive.close

    print(f"{bcolors.OKGREEN}\n{tarball.split('/')[-1].split('.')[0]} build installed to {bcolors.UNDERLINE}{COMPAT_DIR}{bcolors.ENDC}")



def installVersion():
    releases = getEggrollReleases()
    selection = getUserInput(releases)
    downloadURL = getDownloadURL(selection, releases)

    tarball = download(downloadURL)

    decompressTarBall(tarball)

    cleanTempDir(tarball)
    steamRestartPrompt()



def removeVersion():
    installedVersions = getInstalledVersions()

    if not installedVersions:
        print(f'{bcolors.FAIL}No installed GE versions found{bcolors.ENDC}')
        exit()
    
    count = 1

    for v in installedVersions:
        print(f'{count}) {v}')
        count += 1

    print("\n0) Exit")

    selection = int(input('\nSelect version to uninstall: '))
    
    if selection == 0:
        exit()

    if selection > len(installedVersions):
        print(f'{bcolors.FAIL}Invalid Choice{bcolors.ENDC}')
        exit()

    dirToRemove = os.path.join(COMPAT_DIR, installedVersions[selection - 1])

    print(f'Removing {installedVersions[selection - 1]}')
    shutil.rmtree(dirToRemove)
    print(f'{bcolors.OKGREEN}Complete{bcolors.ENDC}')
    steamRestartPrompt()



def isSteamRunning():
    proc = psutil.process_iter()
    for p in proc:
        if p.name() == 'steam':
            return p
    return False



def restartSteam(proc):
    print(f'{bcolors.OKCYAN}Steam is restarting{bcolors.ENDC}')
    proc.terminate()
    while True:
        try: 
            proc.status()
            time.sleep(0.1)
        except:            
            os.system('nohup steam > /dev/null 2>&1 &')
            print(f'{bcolors.OKGREEN}Steam restarted{bcolors.ENDC}')
            break
	



def steamRestartPrompt():
    yesAnswers = ['y', 'yes']
    p = isSteamRunning()
    if p:
        i = input(f'{bcolors.WARNING}Found steam process running. Restart now? y/N{bcolors.ENDC}')
        if i.lower() in yesAnswers:
            restartSteam(p)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group()
    g.add_argument("-i", "--install", action='store_true', help="show a list of available versions to install")    
    g.add_argument("-r", "--remove", action='store_true', help="show a list of installed version to remove")
    g.add_argument("-li", "--listinstalled", action='store_true', help="list installed versions")

    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        parser.exit()
    
    if args.install:
        installVersion()
        
    if args.listinstalled:
        print(getInstalledVersions())

    if args.remove:
        removeVersion()