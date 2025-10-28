from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField

# Create your models here.
class Page(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField(unique=True, blank=True)
	is_published = models.BooleanField(default=False)
	content = RichTextField()
	
 
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify(self.title)
		super().save(*args, **kwargs)
 
	def __str__(self):
		return self.title