import requests, os, json
from pyquery import PyQuery as pq
from datetime import datetime
from exif import Image, DATETIME_STR_FORMAT
from datetime import datetime
from dateutil.parser import parse

print("🌍 Enter MyAlbum URL: ")
url = input()

print("  ⏳ Downloading page...")
page = requests.get(url, headers={'referer': url})
page.raise_for_status()

print("  ⏳ Parsing page...")
rootTag = pq(page.content)
rootJsonString = rootTag('#__NEXT_DATA__').html()
rootJson = json.loads(rootJsonString)

albumTitle = rootJson["props"]["pageProps"]["album"]["data"]	["title"]
print(f"    ℹ️  Album title: {albumTitle}")

contents = rootJson["props"]["pageProps"]["album"]["data"]["contents"]
print(f"    ℹ️  {len(contents)} content item(s) found")

spreads = list(filter(lambda item: item["type"] == "spread", contents))
spreads = list(map(lambda spread: spread["url"], spreads))
print(f"    ℹ️  {len(spreads)} spread URL(s) found")

class ImageData(object):
	def __init__(self, id, url, key):
		self.id = id
		self.url = url
		self.key = key

print("  ⏳ Parsing spreads...")
flat_map = lambda f, xs: [y for ys in xs for y in f(ys)]

images = list()
for spreadUrl in spreads:
	spreadIdStart = spreadUrl.index("/spreads/") + len("/spreads/")
	spreadId = spreadUrl[spreadIdStart:]

	print(f"    ⏳ Downloading and parsing spread {spreadId}...")
	spreadResponse = requests.get(spreadUrl, headers={'referer': url})
	spreadResponse.raise_for_status()
	spreadJson = json.loads(spreadResponse.content)

	pages = spreadJson["pages"]

	layerDatas = list(map(lambda page: page["data"]["layerData"], pages))
	photos = list()
	for data in layerDatas:
		for key in data:
			if key.lower().find("grid") >= 0:
				photos.append(data[key]["style"]["content"]["asset"])

	photos = list(filter(lambda photo: photo["type"] == "photo", photos))
	print(f"      ℹ️  {len(photos)} photo(s) found in spread")

	for photo in photos:
		imageUrl = photo["sizes"][-1]["url"]
		imageId = photo["id"]
		imageKey = photo["key"]
		images.append(ImageData(imageId, imageUrl, imageKey))
		pass
	pass

imagesCount = len(images)
print(f"    ℹ️  {imagesCount} image(s) found\n")

print(f"📂 Enter album directory name (default: {albumTitle}): ")
dirName = input()
if (len(dirName.strip()) == 0):
	dirName = albumTitle.strip()
else:
	dirName = dirName.strip()

if not os.path.isdir(dirName):
    os.makedirs(dirName)
else:
    print("  ⚠️  Folder already exists")

print("  ⏳ Downloading images...")
for image in images:
	print(f"    ⏳ Downloading image {image.id}...")
	exifResponse = requests.get(f"https://myalbum.com/api/v2/album/tZqckzSnbv4Crj/asset/{image.key}/exif")
	exifResponse.raise_for_status()
	exifJson = json.loads(exifResponse.content)

	fileName = exifJson["fileName"]

	imageResponse = requests.get(image.url)
	imageResponse.raise_for_status()
	file = open(f"{dirName}/{fileName}", "wb")
	file.write(imageResponse.content)
	file.close()

	exif = Image(f"{dirName}/{fileName}")
	exif.model = exifJson['cameraModel']
	exif.maker = exifJson['cameraBrand']
	exif.software = exifJson['software']
	exif.exposure_time = exifJson['shutterSpeed']
	exif.focal_length = exifJson['focalLength']
	exif.aperture_value = exifJson['aperture']
	exif.iso_speed = exifJson['iso']
	# exif.image_height = exifJson['height']
	# exif.image_width = exifJson['width']
	exif.image_unique_id = image.id
	exif.image_description = albumTitle
	exif.datetime_original = parse(exifJson['dateTaken']).strftime(DATETIME_STR_FORMAT)

	with open(f"{dirName}/{fileName}", 'wb') as new_image_file:
		new_image_file.write(exif.get_file())

	os.utime(f"{dirName}/{fileName}", (datetime.timestamp(datetime.strptime(exifJson['dateTaken'], '%Y-%m-%dT%H:%M:%S.%fZ')), datetime.timestamp(datetime.strptime(exifJson['dateTaken'], '%Y-%m-%dT%H:%M:%S.%fZ'))))

print("✅  All done!")
