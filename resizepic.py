import os
from io import BytesIO
from PIL import Image, ImageCms


def process_image_directory_hd_lossless(directory_path):
    if not os.path.isdir(directory_path):
        print(f"Error: The directory '{directory_path}' does not exist.")
        return

    supported_extensions = ('.jpg', '.jpeg', '.png')
    image_files = [
        filename for filename in os.listdir(directory_path)
        if os.path.isfile(os.path.join(directory_path, filename))
        and os.path.splitext(filename)[1].lower() in supported_extensions
    ]
    total_images = len(image_files)
    completed_images = 0

    print(f"Scanning, resizing to HD max, and compressing: {directory_path}\n" + "-" * 60)

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        if os.path.isfile(file_path):
            ext = os.path.splitext(filename)[1].lower()

            if ext in ['.jpg', '.jpeg', '.png']:
                try:
                    with Image.open(file_path) as img:
                        # Resize only screenshots; retain original dimensions for all other files.
                        if 'screenshot' in filename.lower():
                            img.thumbnail((1920, 1080), Image.Resampling.LANCZOS)

                        save_kwargs = {}

                        # Preserve orientation and metadata such as copyright tags.
                        exif_data = img.info.get('exif')
                        if exif_data:
                            save_kwargs['exif'] = exif_data
                        if 'icc_profile' in img.info:
                            save_kwargs['icc_profile'] = img.info['icc_profile']

                        if ext in ['.jpg', '.jpeg']:
                            # Quality 88 is a strong visual-quality/high-compression balance.
                            # Progressive JPEGs decode efficiently and optimize well.
                            save_kwargs.update({
                                'format': 'JPEG',
                                'optimize': True,
                                'progressive': True,
                                'quality': 88,
                                'subsampling': 2,
                            })

                        elif ext == '.png':
                            # Convert PNG to JPEG for much smaller, visually similar output.
                            rgba = img.convert('RGBA')
                            rgb_image = Image.new('RGB', rgba.size, (255, 255, 255))
                            rgb_image.paste(rgba, mask=rgba.getchannel('A'))

                            # Convert display-profiled PNG pixels to sRGB before JPEG encoding.
                            icc_profile = img.info.get('icc_profile')
                            if icc_profile:
                                try:
                                    source_profile = ImageCms.ImageCmsProfile(BytesIO(icc_profile))
                                    srgb_profile = ImageCms.createProfile('sRGB')
                                    rgb_image = ImageCms.profileToProfile(
                                        rgb_image,
                                        source_profile,
                                        srgb_profile,
                                        outputMode='RGB',
                                        renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                        intent=ImageCms.Intent.RELATIVE_COLORIMETRIC,
                                        flags=ImageCms.Flags.BLACKPOINT_COMPENSATION,
                                    )
                                    icc_profile = ImageCms.ImageCmsProfile(srgb_profile).tobytes()
                                except Exception:
                                    # Keep the flattened RGB image if the profile is malformed.
                                    pass

                            jpg_path = os.path.splitext(file_path)[0] + '.jpg'
                            save_kwargs = {
                                'quality': 92,
                                'subsampling': 0,
                                'optimize': True,
                                'progressive': True,
                                'format': 'JPEG',
                            }
                            if icc_profile:
                                save_kwargs['icc_profile'] = icc_profile

                            rgb_image.save(jpg_path, **save_kwargs)
                            os.remove(file_path)

                            completed_images += 1
                            print(
                                f"Converted PNG to JPG: {filename} -> "
                                f"{os.path.basename(jpg_path)} "
                                f"— Completed {completed_images}/{total_images}"
                            )
                            continue

                        # Convert only unsupported transparency/color modes for JPEG.
                        image_to_save = img
                        if ext in ['.jpg', '.jpeg'] and img.mode in ('RGBA', 'LA', 'P'):
                            rgb_image = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                rgb_image.paste(img.convert('RGBA'), mask=img.convert('RGBA').getchannel('A'))
                            else:
                                rgb_image.paste(img, mask=img.getchannel('A'))
                            image_to_save = rgb_image

                        image_to_save.save(file_path, **save_kwargs)

                    completed_images += 1
                    print(f"Processed & Compressed: {filename} ({completed_images}/{total_images})")

                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    print("-" * 60 + "\nProcessing complete!")


# --- Example Usage ---
target_directory = '/Users/jithin/Files/untitled/scnrs2'
# target_directory = '/Users/jithin/Desktop/techs/scripts/tests/img/done'

process_image_directory_hd_lossless(target_directory)