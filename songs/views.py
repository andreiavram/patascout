import os

from django.shortcuts import render, redirect

# Create your views here.
from django.urls.base import reverse
from django.views.generic.edit import UpdateView, CreateView
from django.conf import settings
import os

from songs.forms import SongCreateForm, SongTextEditForm
from songs.models import Song


class SongTextEditView(UpdateView):
    model = Song
    template_name = "songs/song_file_form.html"
    form_class = SongTextEditForm

    def form_valid(self, form):
        self.object = form.save(commit=False)

        song_path = os.path.join(settings.SONGS_LIBRARY_DIR, "songs", "{}.sgc".format(self.object.slug))
        with open(song_path, "w") as f:
            f.write(form.cleaned_data["song_code"])

        self.object.file_path = os.path.join("songs", "{}.sgc".format(self.object.slug))
        self.object.save()
        return redirect("songs:song_detail", kwargs={"slug": self.object.slug})


    def get_initial(self):
        data = super(SongTextEditView, self).get_initial()
        song_path = os.path.join(settings.SONGS_LIBRARY_DIR, self.object.file_path)
        with open(song_path, "r") as f:
            data['song_code'] = f.read()

        return data


class SongCreateView(CreateView):
    model = Song
    template_name = "song/song_create_form.html"
    form_class = SongCreateForm

    def form_valid(self, form):
        self.object = form.save(commit=False)

        song_path = os.path.join(settings.SONGS_LIBRARY_DIR, "songs", "{}.sgc".format(self.object.slug))
        with open(song_path, "w") as f:
            f.write(form.cleaned_data["song_code"])

        self.object.file_path = os.path.join("songs", "{}.sgc".format(self.object.slug))
        self.object.save()
        return redirect("songs:song_detail", kwargs={"slug": self.object.slug})
