from django.db import models
from common.slugs import slugify_translit
from ckeditor.fields import RichTextField

# Create your models here.
class Page(models.Model):
	title = models.CharField(max_length=255)
	slug = models.SlugField(unique=True, blank=True)
	is_published = models.BooleanField(default=False)
	content = RichTextField()
	
 
	def save(self, *args, **kwargs):
		if not self.slug:
			self.slug = slugify_translit(self.title)
		super().save(*args, **kwargs)
 
	def __str__(self):
		return self.title
