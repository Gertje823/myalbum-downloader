import requests, os
from datetime import datetime
from exif import Image

print("Enter myalbum url:")
url = input()

r = requests.get(f"{url}/json", headers={'referer': url})
title = r.json()['album']['title']
try:
    os.mkdir(title)
except FileExistsError:
    print("Folder already exists")
for item in r.json()['itemdata']:
    if r.json()['itemdata'][item]['type'] == 1:
        fileName = r.json()['itemdata'][item]['fileName']
        for img in r.json()['itemdata'][item]['sizes']:
            img =img
        print(f"Downloading {fileName}")
        img_url = f"https://thumbs-eu-west-1.myalbum.io/{img[3]}"
        response = requests.get(img_url)
        file = open(f"{title}/{fileName}", "wb")
        file.write(response.content)
        file.close()
        itemdetails_json = requests.get(f"https://myalbum.com/album/{item}/itemdetails").json()
        img = Image(f"{title}/{fileName}")
        img.model = itemdetails_json['details']['cameraModel']
        img.maker = itemdetails_json['details']['cameraBrand']
        img.software = itemdetails_json['details']['software']
        img.exposure_time = itemdetails_json['details']['shutterSpeed']
        img.focal_length = itemdetails_json['details']['focalLength']
        img.aperture_value = itemdetails_json['details']['aperture']


        with open(f"{title}/{fileName}", 'wb') as new_image_file:
            new_image_file.write(img.get_file())
        os.utime(f"{title}/{fileName}", (datetime.timestamp(datetime.strptime(itemdetails_json['details']['dateTaken'], '%Y:%m:%d %H:%M:%S')), datetime.timestamp(datetime.strptime(itemdetails_json['details']['dateTaken'], '%Y:%m:%d %H:%M:%S'))))