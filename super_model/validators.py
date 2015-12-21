import re
from django.forms import ValidationError

def validate_first_is_letter(value):
    if re.search('^[a-zA-Z0-9]+', value) is None:
        raise ValidationError('Имя пользователя должно начинаться с английской буквы или цифры')

def validate_contains_russian(value):
    if re.search('[а-яА-Я]+', value) is not None:
        raise ValidationError('Имя пользователя содержит русские буквы. Допустимо использовать только английские')

def validate_username(value):
    if re.fullmatch('^[a-zA-Z0-9-_\.]*$', value) is None:
        raise ValidationError('Ошибка в имени пользователя.'
                              ' Допустимо использовать только английские буквы, цифры и символы -  _  .')

