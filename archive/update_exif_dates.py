import os
import piexif
from PIL import Image

# Dictionnaire des fichiers avec leurs dates
files_with_dates = {
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2020/IMG_20200116_153547-COLLAGE.jpg': '2020:01:16 15:35:47',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2021/VID_20200118_090151-COLLAGE.jpg': '2020:01:18 09:01:51',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2022/IMG_20190123_144546-COLLAGE.jpg': '2019:01:23 14:45:46',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190114_131908-COLLAGE(1).jpg': '2019:01:14 13:19:08',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190114_131908-COLLAGE.jpg': '2019:01:14 13:19:08',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190724_073226-COLLAGE(1).jpg': '2019:07:24 07:32:26',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190724_073226-COLLAGE.jpg': '2019:07:24 07:32:26',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20201118_173854-COLLAGE.jpg': '2020:11:18 17:38:54',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20211002_180058-COLLAGE.jpg': '2021:10:02 18:00:58',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20190724_072901-COLLAGE.jpg': '2019:07:24 07:29:01',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20191109_113437-COLLAGE.jpg': '2019:11:09 11:34:37',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20191224_191714-COLLAGE.jpg': '2019:12:24 19:17:14',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20240321_101741-COLLAGE.jpg': '2024:03:21 10:17:41',
    'D:/Sauvegardephotos/GooglePhotos2/St raph/IMG_20200115_111903-COLLAGE.jpg': '2020:01:15 11:19:03',
    'D:/Sauvegardephotos/GooglePhotos2/Sélection avec Christelle/IMG_20190122_130336-COLLAGE.jpg': '2019:01:22 13:03:36',
    'D:/Sauvegardephotos/GooglePhotos2/Sélection avec Lucas_/IMG_20191224_191645-COLLAGE.jpg': '2019:12:24 19:16:45',
    'D:/Sauvegardephotos/GooglePhotos2/Photos from 2019/IMG_20190105_172827-COLLAGE.jpg': '2019:01:05 17:28:27'
}

print(' Updating EXIF metadata for COLLAGE files...')
print('=' * 60)

processed = 0
errors = 0

for file_path, date_str in files_with_dates.items():
    if os.path.exists(file_path):
        print(f' {os.path.basename(file_path)}')
        print(f'   Date: {date_str}')
        
        try:
            with Image.open(file_path) as img:
                exif_data = {
                    '0th': {},
                    'Exif': {},
                    'GPS': {},
                    '1st': {},
                    'thumbnail': None
                }
                
                date_bytes = date_str.encode('ascii')
                exif_data['0th'][piexif.ImageIFD.DateTime] = date_bytes
                exif_data['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_bytes
                exif_data['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_bytes
                
                exif_bytes = piexif.dump(exif_data)
                img.save(file_path, exif=exif_bytes)
                
                print('    Success')
                processed += 1
        except Exception as e:
            print(f'    Error: {e}')
            errors += 1
    else:
        print(f'  Not found: {os.path.basename(file_path)}')
        errors += 1
    
    print()

print(f' Summary:')
print(f'    Files processed: {processed}')
print(f'    Errors: {errors}')
print(f'    Total: {len(files_with_dates)}')

if processed > 0:
    print('')
    print(' Metadata update completed!')
    print(' Run analyze_metadata.py to verify changes')
