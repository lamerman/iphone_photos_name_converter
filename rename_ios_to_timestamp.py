#!/usr/bin/env python3

import argparse
import os
import re
from datetime import datetime

import exifread
from pymediainfo import MediaInfo


ImagePattern = re.compile('IMG_[\d]{4}\.(?i)(jpg)')
ImageEPattern = re.compile('IMG_E[\d]{4}\.(?i)(jpg)')
VideoPattern = re.compile('IMG_[\d]{4}\.(?i)(mov)')

ExifDateTimeKey = 'EXIF DateTimeOriginal'


def parse_arguments():
    parser = argparse.ArgumentParser(description='Coverts bad naming of iphone images to a good one. You get '
                                                 'filenames formatted with datetime. Currently it can only work with '
                                                 'compatible format of images and video, high efficient one is not '
                                                 'supported')
    parser.add_argument('--photos-dir', dest='photos_dir', help='Directory where iphone images are.')
    parser.add_argument('--dry-run', dest='dry_run',  help='Do nothing, just pring what you are going to do',
                        action="store_true")
    parser.add_argument('--only-edited-photos', dest='only_edited_photos',
                        help='In case there are two images with the same date, but one of them has E in its name, like '
                             'IMG_100.jpg and IMG_E100.jpg, only E files will be stored. Note: it does not work in 10% '
                             'of cases and it may leave both E and regular files because of simplified logic',
                        action="store_true")

    return parser.parse_args()


def rename_using_exif(dry_run, photos_dir, filename, filename_postfix = 'i'):
    filepath = os.path.join(photos_dir, filename)

    with open(filepath, 'rb') as f:
        tags = exifread.process_file(f)

        if ExifDateTimeKey in tags.keys():
            date_parsed = datetime.strptime(tags[ExifDateTimeKey].values, "%Y:%m:%d %H:%M:%S")
            timestring = date_parsed.strftime("%Y%m%d_%H%M%S" + filename_postfix)

            extension = os.path.splitext(filename)[1]

            new_filepath = os.path.join(photos_dir, timestring + extension)

            if dry_run is not True:
                os.rename(filepath, new_filepath)

            print('{} -> {}'.format(filepath, new_filepath))
        else:
            print('No DateTimeOriginal exif record in image {}'.format(filepath))


def rename_using_mediainfo(dry_run, photos_dir, filename):
    filepath = os.path.join(photos_dir, filename)

    media_info = MediaInfo.parse(filepath)

    try:
        date = media_info.to_data()['tracks'][0]['comapplequicktimecreationdate']
        date_parsed = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
        timestring = date_parsed.strftime("%Y%m%d_%H%M%Si")

        extension = os.path.splitext(filename)[1]

        new_filepath = os.path.join(photos_dir, timestring + extension)

        if dry_run is not True:
            os.rename(filepath, new_filepath)

        print('{} -> {}'.format(filepath, new_filepath))
    except KeyError:
        print('No comapplequicktimecreationdate metadata record in video {}'.format(filepath))


def main():
    args = parse_arguments()

    files = os.listdir(args.photos_dir)
    images_files = list(filter(lambda file: ImagePattern.match(os.path.basename(file)), files))
    images_e_files = list(filter(lambda file: ImageEPattern.match(os.path.basename(file)), files))
    video_files = list(filter(lambda file: VideoPattern.match(os.path.basename(file)), files))

    for f in images_files:
        rename_using_exif(args.dry_run, args.photos_dir, f)

    for f in images_e_files:
        if args.only_edited_photos:
            # regular photos will just be overwritten here by edited ones
            rename_using_exif(args.dry_run, args.photos_dir, f)
        else:
            rename_using_exif(args.dry_run, args.photos_dir, f, filename_postfix='e')

    for f in video_files:
        rename_using_mediainfo(args.dry_run, args.photos_dir, f)


if __name__ == '__main__':
    main()