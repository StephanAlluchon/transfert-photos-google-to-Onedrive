import os
import json
import piexif
from PIL import Image
from datetime import datetime
import shutil
import time
from typing import Optional, Dict

def sanitize_filename(name):
    name = name.replace(" ", "_")
    return name[:30]

def to_deg(value):
    deg = int(value)
    min_float = abs((value - deg) * 60)
    minute = int(min_float)
    sec = int((min_float - minute) * 60 * 100)
    return ((deg, 1), (minute, 1), (sec, 100))

def process_image(image_path, json_path, output_path, rename_file=True):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        timestamp = int(metadata["photoTakenTime"]["timestamp"])
        dt = datetime.utcfromtimestamp(timestamp)
        exif_datetime = dt.strftime("%Y:%m:%d %H:%M:%S")
        date_prefix = dt.strftime("%Y-%m-%d")
        geo = metadata.get("geoData", {})
        lat = geo.get("latitude", 0.0)
        lon = geo.get("longitude", 0.0)
        img = Image.open(image_path)
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
        from piexif import ImageIFD
        if "description" in metadata:
            exif_dict["0th"][ImageIFD.ImageDescription] = metadata["description"].encode("utf-8")
        if "title" in metadata:
            exif_dict["0th"][ImageIFD.XPTitle] = metadata["title"].encode("utf-16le")
        if "people" in metadata and isinstance(metadata["people"], list):
            people_str = ", ".join([p["name"] for p in metadata["people"] if "name" in p])
            exif_dict["0th"][ImageIFD.XPKeywords] = people_str.encode("utf-16le")
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_datetime.encode("utf-8")
        exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = exif_datetime.encode("utf-8")
        exif_dict["0th"][piexif.ImageIFD.DateTime] = exif_datetime.encode("utf-8")
        
        # Traitement GPS - coordonnées uniquement
        if lat != 0.0 or lon != 0.0:
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = b'N' if lat >= 0 else b'S'
            exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = to_deg(abs(lat))
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = b'E' if lon >= 0 else b'W'
            exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = to_deg(abs(lon))
            print(f"   🌍 Coordonnées GPS ajoutées: {lat:.6f}, {lon:.6f}")
        
        original_name = os.path.basename(image_path)
        base_name = os.path.splitext(original_name)[0]
        ext = os.path.splitext(original_name)[1].lower()
        
        if rename_file:
            new_name = f"{date_prefix}_{sanitize_filename(base_name)}{ext}"
        else:
            new_name = original_name
            
        output_file_path = os.path.join(output_path, new_name)
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        exif_bytes = piexif.dump(exif_dict)
        img.save(output_file_path, exif=exif_bytes)
        print(f"✅ {original_name} → {output_file_path}")
    except Exception as e:
        print(f"❌ Erreur avec {image_path}: {e}")

def set_file_datetime(filepath, dt):
    mod_time = time.mktime(dt.timetuple())
    os.utime(filepath, (mod_time, mod_time))
    try:
        import pywintypes
        import win32file
        import win32con
        handle = win32file.CreateFile(
            filepath, win32con.GENERIC_WRITE,
            0, None, win32con.OPEN_EXISTING, 0, 0)
        win32file.SetFileTime(handle, pywintypes.Time(mod_time), None, pywintypes.Time(mod_time))
        handle.close()
    except ImportError:
        pass

def traiter_doublons(duplicates, ext_label):
    if not duplicates:
        print(f"Aucun doublon {ext_label} trouvé.")
        return
    print(f"\nTraitement interactif des doublons {ext_label} :")
    for fn, dirs in duplicates.items():
        print(f"\n{fn} présent dans {len(dirs)} répertoires :")
        for idx, d in enumerate(dirs, 1):
            print(f"  {idx}. {os.path.join(d, fn)}")
        choix = input(f"Quel fichier {fn} souhaitez-vous garder ? (numéro, 0 pour ne rien supprimer) : ").strip()
        if not choix.isdigit():
            print("Choix invalide, aucun fichier supprimé pour ce doublon.")
            continue
        choix = int(choix)
        if choix == 0:
            print("Aucun fichier supprimé pour ce doublon.")
            continue
        if not (1 <= choix <= len(dirs)):
            print("Numéro hors limites, aucun fichier supprimé pour ce doublon.")
            continue
        for idx, d in enumerate(dirs, 1):
            if idx != choix:
                try:
                    os.remove(os.path.join(d, fn))
                    print(f"  Supprimé : {os.path.join(d, fn)}")
                except Exception as e:
                    print(f"  Erreur suppression {os.path.join(d, fn)} : {e}")

def analyze_and_process(source_dir, output_dir):
    # 1. Indexation par nom de base
    files_by_base = {}
    dir_count = 0
    for dirpath, _, filenames in os.walk(source_dir):
        dir_count += 1
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            ext = ext.lower()
            full_path = os.path.join(dirpath, filename)
            # Extensions insensibles à la casse
            if ext in [".jpg", ".jpeg", ".mp4"]:
                base = name
                files_by_base.setdefault(base, {})[ext] = full_path
            elif ext == ".json":
                # Gère tous les types de json (sup, supplemental, mp4)
                if filename.lower().endswith(".supplemental-metadata.json"):
                    base = filename[:-len(".jpg.supplemental-metadata.json")]
                    files_by_base.setdefault(base, {})[".json"] = full_path
                elif filename.lower().endswith(".sup.json"):
                    base = filename[:-len(".sup.json")]
                    files_by_base.setdefault(base, {})[".supjson"] = full_path
                elif filename.lower().endswith(".mp4.supplemental-metadata.json"):
                    base = filename[:-len(".mp4.supplemental-metadata.json")]
                    files_by_base.setdefault(base, {})[".mp4json"] = full_path

    # 2. Statistiques
    total_jpg = 0
    total_mp4 = 0
    jpg_with_json = 0
    jpg_without_json = 0
    mp4_with_json = 0
    mp4_without_json = 0
    for base, files in files_by_base.items():
        if ".mp4" in files:
            total_mp4 += 1
            if ".json" in files:
                mp4_with_json += 1
            else:
                mp4_without_json += 1
        elif ".jpg" in files or ".jpeg" in files:
            total_jpg += 1
            if ".supjson" in files or ".json" in files:
                jpg_with_json += 1
            else:
                jpg_without_json += 1

    print(f"Nombre de sous-répertoires analysés : {dir_count}")
    print(f"Total JPG/JPEG (hors miniatures vidéos) : {total_jpg}")
    print(f"  Avec JSON (.sup.json ou .supplemental-metadata.json) : {jpg_with_json}")
    print(f"  Sans JSON : {jpg_without_json}")
    print(f"Total MP4 : {total_mp4}")
    print(f"  Avec JSON (via miniature .jpg) : {mp4_with_json}")
    print(f"  Sans JSON : {mp4_without_json}")

    # --- Détection des doublons ---
    from collections import defaultdict
    jpg_locations = defaultdict(list)
    mp4_locations = defaultdict(list)
    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            name, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext in [".jpg", ".jpeg"]:
                jpg_locations[filename].append(dirpath)
            elif ext == ".mp4":
                mp4_locations[filename].append(dirpath)

    jpg_duplicates = {fn: dirs for fn, dirs in jpg_locations.items() if len(dirs) > 1}
    mp4_duplicates = {fn: dirs for fn, dirs in mp4_locations.items() if len(dirs) > 1}

    print(f"\nDoublons JPG/JPEG trouvés : {len(jpg_duplicates)}")
    print(f"Doublons MP4 trouvés : {len(mp4_duplicates)}")

    # --- Traitement interactif des doublons ---
    if jpg_duplicates or mp4_duplicates:
        if input("Souhaitez-vous lancer le traitement interactif des doublons ? (o/n) : ").lower() == "o":
            traiter_doublons(jpg_duplicates, "JPG/JPEG")
            traiter_doublons(mp4_duplicates, "MP4")
    else:
        print("Aucun doublon à traiter.")

    # --- Traitement des fichiers et métadonnées ---
    if input("Souhaitez-vous lancer le traitement des fichiers et métadonnées ? (o/n) : ").lower() != "o":
        print("Opération annulée.")
        return
    
    # --- Option de renommage ---
    rename_files = input("Souhaitez-vous renommer les fichiers avec la date en préfixe ? (o/n) : ").lower() == "o"
    
    print("\n🌍 TRAITEMENT GPS")
    print("Les coordonnées GPS seront automatiquement importées depuis les fichiers JSON")
    print("et ajoutées aux métadonnées EXIF des photos.")
    print("💡 Pour le géocodage (conversion coordonnées → noms de lieux), utilisez analyze-modify_metadata.py")

    # 3. Traitement
    copied_jpg = 0
    treated_jpg = 0
    copied_mp4 = 0
    total_photos = treated_jpg + copied_jpg
    print(f"Total photos traitées ou copiées : {total_photos}")
    for base, files in files_by_base.items():
        # Vidéo
        if ".mp4" in files:
            rel_dir = os.path.relpath(os.path.dirname(files[".mp4"]), source_dir)
            out_dir = os.path.join(output_dir, rel_dir)
            os.makedirs(out_dir, exist_ok=True)
            dest_mp4 = os.path.join(out_dir, os.path.basename(files[".mp4"]))
            shutil.copy2(files[".mp4"], dest_mp4)
            copied_mp4 += 1
            json_path = files.get(".json") or files.get(".mp4json")
            if json_path:
                with open(json_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                timestamp = int(metadata["photoTakenTime"]["timestamp"])
                dt = datetime.utcfromtimestamp(timestamp)
                set_file_datetime(dest_mp4, dt)
            print(f"🎬 Vidéo copiée : {files['.mp4']} → {dest_mp4}")
            # Miniature
            for ext_img in [".jpg", ".jpeg"]:
                if ext_img in files and os.path.exists(files[ext_img]):
                    dest_jpg = os.path.join(out_dir, os.path.basename(files[ext_img]))
                    shutil.copy2(files[ext_img], dest_jpg)
                    print(f"🖼️ Miniature copiée : {files[ext_img]} → {dest_jpg}")
                    break
            else:
                print(f"ℹ️ Pas de miniature JPG/JPEG trouvée pour {files['.mp4']}")
        # Photo seule
        elif ".jpg" in files or ".jpeg" in files:
            ext_img = ".jpg" if ".jpg" in files else ".jpeg"
            rel_dir = os.path.relpath(os.path.dirname(files[ext_img]), source_dir)
            out_dir = os.path.join(output_dir, rel_dir)
            os.makedirs(out_dir, exist_ok=True)
            if ".supjson" in files:
                process_image(files[ext_img], files[".supjson"], out_dir, rename_files)
                treated_jpg += 1
            elif ".json" in files:
                process_image(files[ext_img], files[".json"], out_dir, rename_files)
                treated_jpg += 1
            else:
                dest_jpg = os.path.join(out_dir, os.path.basename(files[ext_img]))
                shutil.copy2(files[ext_img], dest_jpg)
                copied_jpg += 1
                print(f"📁 Photo copiée sans JSON : {files[ext_img]} → {dest_jpg}")

    print(f"Nombre de photos traitées avec JSON : {treated_jpg}")
    print(f"Nombre de photos copiées sans JSON : {copied_jpg}")
    print(f"Nombre de vidéos copiées : {copied_mp4}")
    print(f"Vérification : total_jpg attendu = {total_jpg}, total traité = {treated_jpg + copied_jpg}")
    if total_jpg != (treated_jpg + copied_jpg):
        print("⚠️ Attention : le nombre de photos traitées ne correspond pas au nombre attendu !")
    else:
        print("✅ Nombre de photos traitées conforme au nombre attendu.")

# --- Utilisation ---
default_source = "D:/SAuvegardephotos/GooglePhotos"
default_output = "D:/Sauvegardephotos/GooglePhotos2"

source = input(f"Dossier d'origine [{default_source}] : ").strip()
if not source:
    source = default_source

output = input(f"Dossier de destination [{default_output}] : ").strip()
if not output:
    output = default_output

analyze_and_process(source, output)