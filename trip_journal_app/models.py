from django.db import models
import json
import os
from TripJournal.settings import (IMAGE_SIZES, STORED_IMG_DOMAIN,
                                  IMG_STORAGE, TEMP_DIR)
from trip_journal_app.utils.resize_image import resize_and_save_pics
from django.contrib.auth.models import User


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.name


class Story(models.Model):
    title = models.CharField(max_length=300)
    date_travel = models.DateField()
    date_publish = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    track = models.TextField(blank=True, null=True)
    rating = models.FloatField(blank=True, null=True)
    published = models.BooleanField(default=False)
    user = models.ForeignKey(User)
    tags = models.ManyToManyField(Tag)

    def __unicode__(self):
        return self.title

    def get_tags(self):
        return self.tags.all()

    def get_comments(self):
        return Comment.objects.filter(story=self.id)

    def get_map_artifacts(self):
        return Map_artifact.objects.filter(story=self.id)

    def get_pictures_urls(self, max_size):
        '''
        Returns a dictionary where pictures ids are keys and stored pictures
        of appropriate size are values.
        '''
        pictures = Picture.objects.filter(story=self.id)
        return dict([
            (pic.id, pic.get_stored_pic_by_size(max_size))
            for pic in pictures
        ])

    def get_text_with_pic_urls(self, max_pic_size):
        '''
        Takes story text and desirable size of pictures and adds
        urls to respective block of content.
        '''
        pics = self.get_pictures_urls(max_pic_size)
        text = json.loads(self.text, encoding='utf8')
        for block in text:
            if block[u'type'] == u'img':
                block[u'url'] = pics[block[u'id']]
        return text


class Picture(models.Model):
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    story = models.ForeignKey(Story)
    SIZES = IMAGE_SIZES

    def __unicode__(self):
        return self.name

    def get_stored_pic_by_size(self, max_accatible_size):
        '''
        Retrun the object Stored picture with the greatest size
        not bigger than max_accatible_size. If there isn't smaller
        pictures returns the smallest from available.
        '''
        story_pics = Stored_picture.objects.filter(picture=self.id)
        accetable_pics = story_pics.filter(size__lt=max_accatible_size)
        if accetable_pics:
            pic = accetable_pics.order_by('size').last()
            return pic
        return story_pics.order_by('size').first()

    def save_in_sizes(self, image):
        '''
        Stores info about picture and it's thumbnails in database
        and writes them to path defined in Stored_picture class.
        '''
        # check if Pictures directory exists
        if not os.path.exists(Stored_picture.SAVE_PATH):
            os.makedirs(Stored_picture.SAVE_PATH)

        # temporary storing file
        img_name = image.name
        file_name = os.path.join(TEMP_DIR, img_name)
        with open(file_name, 'w') as img_file:
            for chunk in image.chunks():
                img_file.write(chunk)

        # resizing original image
        names_and_sizes = resize_and_save_pics(
            file_name, str(self.id), self.SIZES, Stored_picture.SAVE_PATH
        )
        for name, size in names_and_sizes:
            stored_pic = Stored_picture(picture=self, size=size)
            stored_pic.url = name
            stored_pic.save()

        # delete temp file
        os.remove(file_name)


class Stored_picture(models.Model):
    picture = models.ForeignKey(Picture)
    size = models.IntegerField()
    _url = models.CharField(max_length=2000)
    SAVE_PATH = IMG_STORAGE
    URL_PREFIX = STORED_IMG_DOMAIN

    @property
    def url(self):
        return self.URL_PREFIX + self._url

    @url.setter
    def url(self, value):
        self._url = value

    def __unicode__(self):
        return self.url


class Comment(models.Model):
    text = models.CharField(max_length=1000)
    user = models.ForeignKey(User)
    story = models.ForeignKey(Story)
    time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.text


class Map_artifact(models.Model):
    text = models.TextField()
    story = models.ForeignKey(Story)
    latitude = models.FloatField()
    longitude = models.FloatField()
    name = models.CharField(max_length=45, unique=True)

    def __unicode__(self):
        return self.name

