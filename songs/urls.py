from django.conf.urls import url
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from songs.models import Song
from songs.views import SongCreateView, SongTextEditView

urlpatterns = [
    url("song/list/$", ListView.as_view(model=Song), name="song_list"),
    url("song/(?P<slug>[-\w]+)/$", DetailView.as_view(model=Song), name="song_detail"),
    url("song/(?P<slug>[-\w]+)/edit/$", SongTextEditView.as_view(), name="song_code_edit"),
    url("song/new/$", SongCreateView.as_view(), name="song_add")
]
