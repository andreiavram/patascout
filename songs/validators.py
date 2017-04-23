# coding: utf-8
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


def validate_latex_free(string):
    """ Return true if one of the LaTeX special characters is in the string """
    tex_char, message = forbidden_latex_chars()
    for char in tex_char:
        if char in string:
            raise ValidationError(message)


def forbidden_latex_chars():
    """ Return the LaTeX special characters and a corresponding error string """

    tex_char = ['\\', '{', '}', '&', '[', ']', '^', '~']
    chars = ', '.join(['"{char}"'.format(char=char) for char in tex_char])
    message = _(u"Următoarele caractere sunt interzise și trebuie scoase : {chars}.".format(chars=chars))
    return tex_char, message


def latex_free_attributes():
    tex_char, message = forbidden_latex_chars()
    escaped_chars = ''.join(['\\{char}'.format(char=char) for char in tex_char])
    escaped_chars = '[^' + escaped_chars + ']*'

    error_message = message.replace("'", "\\'")

    return {
        'pattern': escaped_chars,
        'title': error_message
    }
