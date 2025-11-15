import cv2
import os
import numpy as np

class PathDetector:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = cv2.imread(image_path)

        if self.image is None:
            raise ValueError(f"Bild konnte nicht geladen werden: {image_path}")

    def process_and_save(self):
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)

        # HSV-Bereich für Blau definieren
        lower_blue = (100, 100, 50)
        upper_blue = (140, 255, 255)
        mask = cv2.inRange(hsv, lower_blue, upper_blue)

        # Nur die blauen Bereiche extrahieren
        result = cv2.bitwise_and(self.image, self.image, mask=mask)

        # Optional: Konturen zeichnen (Pfad)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours, -1, (0, 0, 255), 2)

        # Gespeichertes Bild vorbereiten
        base, ext = os.path.splitext(self.image_path)
        output_path = f"{base}_processed{ext}"
        cv2.imwrite(output_path, result)
        return output_path

    def get_position_for_semester(self, semester_count):
        if not self.image_path.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            raise ValueError("Nur Rasterbilder (PNG, JPG, WebP) sind für die Pfaderkennung geeignet.")
        try:
            hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
            hsv = cv2.GaussianBlur(hsv, (9, 9), 0)
        except Exception as e:
            raise ValueError(f"Fehler bei der HSV-Umwandlung: {e}")

        try:
            lower_blue = (90, 50, 40)
            upper_blue = (150, 255, 255)
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
        except Exception as e:
            raise ValueError(f"Fehler beim Erzeugen der Blaufiltermaske: {e}")

        def get_dark_mask(hsv_img):
            try:
                lower_dark = (0, 0, 0)
                upper_dark = (180, 255, 60)
                mask = cv2.inRange(hsv_img, lower_dark, upper_dark)
                mask = cv2.dilate(mask, None, iterations=2)
                mask = cv2.erode(mask, None, iterations=2)
                return mask
            except Exception as e:
                raise ValueError(f"Fehler beim Erzeugen der Dunkelmaske: {e}")

        try:
            mask_dark = get_dark_mask(hsv)
        except Exception as e:
            raise ValueError(str(e))

        def get_sign_mask(hsv_img):
            try:
                # Gelbtonbereich für Schilder (z. B. kräftiges Gelb)
                lower_yellow = (20, 100, 100)
                upper_yellow = (40, 255, 255)
                mask = cv2.inRange(hsv_img, lower_yellow, upper_yellow)
                return mask
            except Exception as e:
                raise ValueError(f"Fehler beim Erzeugen der Schildmaske: {e}")

        try:
            mask_sign = get_sign_mask(hsv)
        except Exception as e:
            raise ValueError(str(e))

        try:
            debug_dir = "debug_masks"
            os.makedirs(debug_dir, exist_ok=True)
            cv2.imwrite(os.path.join(debug_dir, "mask_blue.png"), mask_blue)
            cv2.imwrite(os.path.join(debug_dir, "mask_sign.png"), mask_sign)
            cv2.imwrite(os.path.join(debug_dir, "mask_dark.png"), mask_dark)
        except Exception as e:
            print(f"Warnung: Debug-Masken konnten nicht gespeichert werden: {e}")

        try:
            points = cv2.findNonZero(mask_blue)
            if points is None or len(points) < 6:
                raise ValueError("Nicht genügend Pfadpunkte gefunden.")
            sorted_points = sorted(points[:, 0], key=lambda p: (p[0] + p[1]))
        except Exception as e:
            raise ValueError(f"Fehler bei Pfadpunkt-Ermittlung: {e}")

        def is_near_masked(px, py, masks, radius=8):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x, y = px + dx, py + dy
                    if 0 <= x < masks[0].shape[1] and 0 <= y < masks[0].shape[0]:
                        for mask in masks:
                            if mask[y, x] != 0:
                                return True
            return False

        try:
            filtered_points = [pt for pt in sorted_points if not is_near_masked(pt[0], pt[1], [mask_dark, mask_sign])]
            if not filtered_points:
                raise ValueError("Alle Pfadpunkte befinden sich auf oder nahe dunklen Bereichen oder Schildern.")
            idx = int(len(filtered_points) * (semester_count / 6))
            idx = min(idx, len(filtered_points) - 1)
            px, py = filtered_points[idx]
        except Exception as e:
            raise ValueError(f"Fehler bei Punktfilterung oder Indexwahl: {e}")

        try:
            if mask_dark[py, px] != 0:
                raise ValueError("Zielposition befindet sich auf einem dunklen Bereich.")
            h, w = self.image.shape[:2]
            x_percent = px / w
            y_percent = py / h
            return x_percent, y_percent
        except Exception as e:
            raise ValueError(f"Fehler bei Zielberechnung: {e}")
