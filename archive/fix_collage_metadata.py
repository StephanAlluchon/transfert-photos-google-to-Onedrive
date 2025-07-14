#!/usr/bin/env python3
"""
Script Python pour modifier les métadonnées EXIF des fichiers COLLAGE
Ce script utilise piexif pour ajouter les dates extraites des noms de fichiers
"""

import os
import sys
from datetime import datetime
import piexif
from PIL import Image
import re

def extract_date_from_filename(filename):
    """Extraire la date du nom de fichier au format IMG_YYYYMMDD_HHMMSS"""
    # Pattern pour IMG_YYYYMMDD_HHMMSS
    pattern = r'IMG_(\d{8})_(\d{6})'
    match = re.search(pattern, filename)
    
    if match:
        date_str = match.group(1)  # YYYYMMDD
        time_str = match.group(2)  # HHMMSS
        
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])
        
        return datetime(year, month, day, hour, minute, second)
    
    # Pattern pour VID_YYYYMMDD_HHMMSS
    pattern = r'VID_(\d{8})_(\d{6})'
    match = re.search(pattern, filename)
    
    if match:
        date_str = match.group(1)  # YYYYMMDD
        time_str = match.group(2)  # HHMMSS
        
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])
        
        return datetime(year, month, day, hour, minute, second)
    
    return None

def set_exif_date(file_path, date_time):
    """Modifier les métadonnées EXIF d'un fichier"""
    try:
        print(f" Processing: {os.path.basename(file_path)}")
        print(f"   Setting date: {date_time.strftime('%Y:%m:%d %H:%M:%S')}")
        
        # Ouvrir l'image
        with Image.open(file_path) as img:
            # Obtenir les données EXIF existantes ou créer nouvelles
            try:
                exif_data = piexif.load(img.info.get('exif', b''))
            except:
                # Créer de nouvelles données EXIF si elles n'existent pas
                exif_data = {
                    '0th': {},
                    'Exif': {},
                    'GPS': {},
                    '1st': {},
                    'thumbnail': None
                }
            
            # Formatage de la date pour EXIF
            date_str = date_time.strftime('%Y:%m:%d %H:%M:%S')
            date_bytes = date_str.encode('ascii')
            
            # Définir les champs de date EXIF
            exif_data['0th'][piexif.ImageIFD.DateTime] = date_bytes
            exif_data['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_bytes
            exif_data['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_bytes
            
            # Convertir en bytes
            exif_bytes = piexif.dump(exif_data)
            
            # Sauvegarder l'image avec les nouvelles métadonnées
            img.save(file_path, exif=exif_bytes)
            
            print(f"    Success")
            return True
            
    except Exception as e:
        print(f"    Error: {str(e)}")
        return False

def main():
    """Fonction principale"""
    print(" EXIF Metadata Updater for COLLAGE Files")
    print("=" * 60)
    
    # Fichiers à traiter avec leurs chemins
    files_to_process = [
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2020/IMG_20200116_153547-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2021/VID_20200118_090151-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2022/IMG_20190123_144546-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190114_131908-COLLAGE(1).jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190114_131908-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190724_073226-COLLAGE(1).jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20190724_073226-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20201118_173854-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2023/IMG_20211002_180058-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20190724_072901-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20191109_113437-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20191224_191714-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2024/IMG_20240321_101741-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/St raph/IMG_20200115_111903-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Sélection avec Christelle/IMG_20190122_130336-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Sélection avec Lucas_/IMG_20191224_191645-COLLAGE.jpg",
        "D:/Sauvegardephotos/GooglePhotos2/Photos from 2019/IMG_20190105_172827-COLLAGE.jpg"
    ]
    
    processed_count = 0
    error_count = 0
    
    for file_path in files_to_process:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            extracted_date = extract_date_from_filename(filename)
            
            if extracted_date:
                if set_exif_date(file_path, extracted_date):
                    processed_count += 1
                else:
                    error_count += 1
            else:
                print(f"  Could not extract date from: {filename}")
                error_count += 1
        else:
            print(f"  File not found: {os.path.basename(file_path)}")
            error_count += 1
        
        print()
    
    print(" Summary:")
    print(f"    Files processed: {processed_count}")
    print(f"    Files with errors: {error_count}")
    print(f"    Total files: {len(files_to_process)}")
    
    if processed_count > 0:
        print("")
        print(" Metadata update completed!")
        print(" You can now re-run analyze_metadata.py to verify the changes")
    else:
        print("")
        print(" No files were processed")

if __name__ == "__main__":
    main()
