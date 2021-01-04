from ariadne import convert_kwargs_to_snake_case
from django.core.exceptions import ObjectDoesNotExist

from impacts.models import Indicator, Entry, Impact


@convert_kwargs_to_snake_case
def resolve_indicators(*_):
    return Indicator.objects.all()


@convert_kwargs_to_snake_case
def resolve_indicator(*_, id):
    indicator = None
    # TODO: move this code in the model
    if id is not None:
        try:
            indicator = Indicator.objects.get(pk=id)
        except ObjectDoesNotExist:
            pass
    return indicator


@convert_kwargs_to_snake_case
def resolve_entries(*_):
    return Entry.objects.all()


@convert_kwargs_to_snake_case
def resolve_entry(*_, id):
    entry = None
    # TODO: move this code in the model
    if id is not None:
        try:
            entry = Entry.objects.get(pk=id)
        except ObjectDoesNotExist:
            pass
    return entry


@convert_kwargs_to_snake_case
def resolve_impact(*_, entry_i_d, indicator_i_d):
    impact = None
    # TODO: move this code in the model
    if entry_i_d is not None and indicator_i_d is not None:
        try:
            impact = Impact.objects.get(entry=entry_i_d, indicator=indicator_i_d)
        except ObjectDoesNotExist:
            pass
    return impact
