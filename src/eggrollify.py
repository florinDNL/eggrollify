import os
import sys
import glob
import shutil
import tarfile
import argparse
import requests


HOME = os.path.expanduser("~")
TEMP_FOLDER = os.path.join(os.getcwd(), 'tempfolder')
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
    print('Steam directory not found. Is Steam installed?')
    exit()

COMPAT_DIR = os.path.join(steamDir, 'steam/compatibilitytools.d')



def getInstalledVersions():
    protonDirs = os.listdir(COMPAT_DIR)
    protonGeDirs = []

    for dir in protonDirs:
        if 'GE-' in dir:
            protonGeDirs.append(dir)

    return protonGeDirs



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
        print('Invalid Choice')
        exit()
    
    if selection == 0:
        exit()

    return selection



def getDownloadURL(selection, releases):
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
        print(f"Downloading {filename} to {TEMP_FOLDER}")        
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



def cleanTempDir():
    rm_files = glob.glob(os.path.join(TEMP_FOLDER, '*'), recursive=True)
    for f in rm_files:
        os.remove(f)
    print('Temporary download deleted.')



def decompressTarBall(tarball):    
    archive = tarfile.open(tarball)

    print('\nExtracting Proton-GE build')

    archive.extractall(COMPAT_DIR)
    archive.close

    print(f'\nProton-GE build installed to {COMPAT_DIR}')



def installVersion():
    releases = getEggrollReleases()
    selection = getUserInput(releases)
    downloadURL = getDownloadURL(selection, releases)

    tarball = download(downloadURL)

    decompressTarBall(tarball)

    cleanTempDir()



def removeVersion():
    installedVersions = getInstalledVersions()

    if not installedVersions:
        print('No installed GE versions found')
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
        print('Invalid Choice')
        exit()

    dirToRemove = os.path.join(COMPAT_DIR, installedVersions[selection - 1])

    print(f'Removing {installedVersions[selection - 1]}')
    shutil.rmtree(dirToRemove)
    print('Complete')



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