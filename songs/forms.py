from django.forms.fields import CharField
from django.forms.models import ModelForm
from django.forms.widgets import Textarea

from songs.models import Song


class SongCreateForm(ModelForm):
    class Meta:
        model = Song
        fields = ("title", "language", "artist")

    song_code = CharField(widget=Textarea, required=True)


class SongTextEditForm(ModelForm):
    class Meta:
        model = Song
        fields = ("title", "language", "artist")

    song_code = CharField(widget=Textarea, required=True)

