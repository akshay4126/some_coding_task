from django.db import models
from django.core.exceptions import FieldError


# Model definitions


class Geography(models.Model):
    id = models.CharField(primary_key=True, editable=False, max_length=36)
    short_name = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.short_name

    def save(self, **kwargs):
        if not self.id:
            raise FieldError('Error: Can not save Geography object, missing required field "id"')


class Indicator(models.Model):
    method = models.CharField(max_length=45)
    category = models.CharField(max_length=45)
    indicator = models.CharField(max_length=45)
    unit = models.CharField(max_length=45)

    def __str__(self):
        return '%s__%s__%s__%s' % (self.method, self.category, self.indicator, self.unit)


class Entry(models.Model):
    product_name = models.CharField(max_length=255)
    unit = models.CharField(max_length=45)
    quantity = models.FloatField(default=1.0)
    geography = models.ForeignKey(Geography, related_name='entries',
                                  on_delete=models.CASCADE)

    def __str__(self):
        return self.product_name


class Impact(models.Model):
    indicator = models.ForeignKey(Indicator, related_name='impacts',
                                  on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, related_name='impacts',
                              on_delete=models.CASCADE)
    coefficient = models.FloatField(default=0.0)

    def __str__(self):
        return str('%s__%s__%lf' % (self.indicator, self.entry, self.coefficient))
