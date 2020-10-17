from django.core.exceptions import ValidationError


def validate_file_size(file):

    imagesize = file.file.size
    limit = 1
    if imagesize > limit*1024*1024:
        raise ValidationError(
                'Максимальный разрешенный размер файла %sMB' % str(limit))
