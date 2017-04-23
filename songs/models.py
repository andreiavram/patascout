# coding: utf-8
import hashlib
import re
import os

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONField

from songs.validators import validate_latex_free


class Artist(models.Model):
    name = models.CharField(max_length=255, verbose_name=(_("Nume")))
    slug = models.SlugField(max_length=255, unique=True)

    class Meta:
        verbose_name = _("Artist")
        verbose_name_plural = _("Artiști")
        ordering = ["name"]

    def str(self):
        return self.name


class Song(models.Model):
    title = models.CharField(max_length=255, verbose_name=_("Titlu"))
    slug = models.SlugField(max_length=255, unique=True)

    language = models.CharField(max_length=2, null=True)

    artist = models.ForeignKey(Artist, null=True, blank=True)
    file_path = models.FilePathField(path=os.path.join(settings.SONGS_LIBRARY_DIR, "songs"))

    items_in_songbook = GenericRelation('ItemsInSongbook', content_type_field='item_type', object_id_field='item_id')

    class Meta:
        verbose_name = _("Cântec")
        verbose_name_plural = _("Cântece")

    def str(self):
        return self.title


class Section(models.Model):
    name = models.CharField(max_length=200, verbose_name=_(u"nom de section"), validators=[validate_latex_free, ])
    items_in_songbook = GenericRelation('ItemsInSongbook', content_type_field='item_type', object_id_field='item_id')

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.full_clean()
        super(Section, self).save(*args, **kwargs)


class SongBook(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    items = models.ManyToManyField(ContentType, blank=True, through="ItemsInSongbook")

    owner = models.ForeignKey(get_user_model())

    def str(self):
        return "{} - {}".format(self.title, self.owner)

    def hash(self):
        return hashlib.sha1(str(sorted(self.get_as_json().items())).encode()).hexdigest()

    def count_songs(self):
        return ItemsInSongbook.objects.filter(songbook=self, item_type=ContentType.objects.get_for_model(Song)).count()

    def count_artists(self):
        songs = ItemsInSongbook.objects.prefetch_related('item')
        songs = songs.filter(songbook=self, item_type=ContentType.objects.get_for_model(Song))

        artists = set()
        for song in songs:
            artists.add(song.item.artist_id)
        return len(artists)

    def count_section(self):
        sections = ItemsInSongbook.objects.filter(songbook=self, item_type=ContentType.objects.get_for_model(Section))
        return sections.count()

    def count_items(self):
        return ItemsInSongbook.objects.filter(songbook=self).count()

    def fill_holes(self):
        """fill the holes in the rank after deletion
        If their is two equal ranks, items are randomly sorted !
        """
        rank = 1
        item_list = ItemsInSongbook.objects.filter(songbook=self)
        for item in item_list:
            if not item.rank == rank:
                item.rank = rank
                item.save()
            rank += 1

    def add_section(self, name, rank=None):
        section = Section.objects.create(name=name)
        section.save()

        ItemsInSongbook.objects.create(songbook=self, item=section, rank=rank)

    def get_as_json(self):
        d = {"subtitle": self.description,
             "title": self.title,
             "author": str(self.owner),
             "content": [],
             "authwords": {
               "sep": ["and", "et"]
             }
        }

        #   Let the newlines of the description be compiled in Latex
        d["subtitle"] = re.sub(r'(\r\n|\r|\n)', "%\r\n\\\\newline%\r\n", d["subtitle"])

        items = ItemsInSongbook.objects.filter(songbook=self).order_by("rank").values_list("item_id", "item_type")
        item_ids = [i[0] for i in items]
        item_types = dict(items)

        types = {item_type: item.id for item_type, item in ContentType.objects.get_for_models(Song, Section).items()}

        song_ids = [i[0] for i in items if i[1] == types[Song]]
        song_paths = dict(Song.objects.filter(id__in=song_ids).values_list("id", "file_path"))

        section_ids = [i[0] for i in items if i[1] == types[Section]]
        sections = dict(Section.objects.filter(id__in=section_ids).values_list("id", "name"))

        for item_id in item_ids:
            if item_types[item_id] == types[Song]:
                d["content"].append(str(song_paths[item_id]))
            elif item_types[item_id] == types[Section]:
                d["content"].append(["songsection", sections[item_id]])

        return d


class Papersize(models.Model):
    """
    This class holds paper information for generating a songbook.
    All size are in millimetters..
    """

    name = models.CharField(max_length=200)

    width = models.PositiveIntegerField(_("Lățime"), help_text=_("în mm"))
    height = models.PositiveIntegerField(_("Hauteur"), help_text=_("în mm"))

    left = models.PositiveIntegerField(_("Margine stânga"), help_text=_("în mm"), default=15)
    right = models.PositiveIntegerField(_("Margine dreapta"), help_text=_("în mm"), default=15)
    top = models.PositiveIntegerField(_("Margine sus"), help_text=_("în mm"), default=15)
    bottom = models.PositiveIntegerField(_("Margine jos"), help_text=_("în mm"), default=15)
    bindingoffset = models.PositiveIntegerField(_("Margine legare"), help_text=_("în mm"), default=0)

    class Meta:
        verbose_name = _("Papier")

    def __str__(self):
        return self.name

    def latex_geometry(self, landscape_orientation=False):
        """Return a list containing the geometry properties for the papersize"""

        width = self.width
        height = self.height

        # Should the page be rotated clockwise
        rotate_page = landscape_orientation and height >= width

        if rotate_page:
            width, height = height, width

        geometry = list()

        geometry.append("paperwidth=" + str(width) + "mm")
        geometry.append("paperheight=" + str(height) + "mm")

        geometry.append("asymmetric")

        fields = [
            'top',
            'right',
            'bottom',
            'left',
            'bindingoffset',
        ]

        rotated_fields = [
            'right',
            'bottom',
            'left',
            'top',
            'bindingoffset',
        ]

        for idx, field in enumerate(fields):
            if rotate_page:
                geometry.append(rotated_fields[idx] + "=" + str(getattr(self, field)) + "mm")
            else:
                geometry.append(field + "=" + str(getattr(self, field)) + "mm")

        return geometry


class Layout(models.Model):
    """
    This class holds layout information for generating a songbook.
    """

    BOOKTYPES = (
        ("chorded", _(u"Cu acorduri")),
        ("lyric", _(u"Doar versuri"))
    )

    owner = models.ForeignKey(get_user_model(), related_name='layouts', blank=True)

    booktype = models.CharField(max_length=10, choices=BOOKTYPES, default="chorded", verbose_name=_(u"tip de carte"))
    papersize = models.ForeignKey(Papersize, related_name='layouts', default=1)
    bookoptions = JSONField(default={}, blank=True)
    other_options = JSONField(default={}, blank=True)

    template = models.CharField(max_length=255, default="data.tex", verbose_name=_(u"template"))

    def name(self):
        if self.other_options['orientation'] == 'portrait':
            name = _('{papername} Portrait').format(papername=self.papersize.name)
        else:
            name = _('{papername} Landscape').format(papername=self.papersize.name)
        return name

    def booktype_name(self):
        return dict(self.BOOKTYPES)[self.booktype]

    def get_as_json(self):
        layout = dict(
            booktype=self.booktype,
            bookoptions=self.bookoptions,
            template=self.template
        )

        layout.update(self.other_options)
        landscape_orientation = (self.other_options['orientation'] == 'landscape')
        geometry = self.papersize.latex_geometry(landscape_orientation)
        layout['geometry'] = ",\n  ".join(geometry)

        if landscape_orientation and self.papersize.height >= self.papersize.width:
            used_width = self.papersize.height
        else:
            used_width = self.papersize.width

        if used_width >= 297:
            layout['column_adjustment'] = 'one_more'
        elif used_width <= 148:
            layout['column_adjustment'] = 'only_one'
        else:
            layout['column_adjustment'] = 'none'
        return layout

    class Meta:
        verbose_name = _(u"Format")
        ordering = ["owner_id", "id"]


class ItemsInSongbook(models.Model):
    """Items in the songbooks model
    Every kind of item can be add : section, songs, images, etc.
    """
    item_type = models.ForeignKey(ContentType)
    item_id = models.PositiveIntegerField()
    item = GenericForeignKey('item_type', 'item_id')

    songbook = models.ForeignKey(SongBook)
    rank = models.IntegerField(_(u"position"))

    def __unicode__(self):
        data = dict(item=self.item, item_type=self.item_type, songbook=self.songbook)
        return _('"{item_type}" : "{item}", în "{songbook}"').format(**data)

    class Meta:
        ordering = ["rank"]
        unique_together = ('item_id', 'item_type', 'songbook',)

    def save(self, *args, **kwargs):
        # automatically add a rank, if needed
        if not self.rank:
            count = self.songbook.count_items()
            self.rank = count + 1
        super(ItemsInSongbook, self).save(*args, **kwargs)