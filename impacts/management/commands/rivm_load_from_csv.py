from django.core.management.base import BaseCommand, CommandError
from impacts.models import Geography, Entry, Indicator, Impact
import csv
import random
import re
from enum import Enum, auto

# Next 3 TODO
# 1: Use celery-beat or celery to asychronous file import
# 2: mini-batch the database writes
# 3: Asynchronous status report

csv_import_format = {
    'RIVM2016.V1': {
        'geo_key_regex': re.compile('\[(.+?)\]'),
        'INDICATOR_FIELD_SEPARATOR': ':',
        'INDICATOR_FIELD_COUNT': 3,
        'ENTRY_FIELD_SEPARATOR': ',',
        'ENTRY_FIELD_COUNT': 4,
        'INDICATOR_COLUMN_START_INDEX': 5
    }
}


class TaskStage(Enum):
    TASK_ACCEPTED = auto()
    TASK_CSV_LOADED = auto()
    TASK_PRE_PROCESSED = auto()
    TASK_PROCESSING_ROWS = auto()
    TASK_POST_PROCESSING = auto()
    TASK_FINISHED_SUCCESS = auto()
    TASK_FINISHED_FAILURE = auto()


class Command(BaseCommand):
    help = 'Loads RIVM data from CSV file'
    csv_loader_stats = {
        'indicators_new': 0,
        'indicators_existing': 0,

        'entries_new': 0,
        'entries_existing': 0,

        'impacts_new': 0,
        'impacts_existing': 0
    }
    task_stage = None

    # Local cache for indicators parsed from the first two rows of the CSV file
    # {
    #   column_index: Indicator, ...
    # }
    indicator_cache = {}

    rivm_format = None
    csv_path = None
    csv_reader = None

    processed_rows = 0
    progress_update_interval = 10

    # Sample constants, parsers for data validation
    # TODO: Refactor RIVM format validors and constants
    geo_key_regex = None
    INDICATOR_FIELD_SEPARATOR = ':'
    INDICATOR_FIELD_COUNT = 3
    ENTRY_FIELD_SEPARATOR = ','
    ENTRY_FIELD_COUNT = 4
    INDICATOR_COLUMN_START_INDEX = 5

    def add_arguments(self, parser):
        parser.add_argument('csv_data_file')
        # TODO: place holder for reading csv format version
        # parser.add_argument('rivm_format')

    def handle(self, *args, **options):

        self.task_stage = TaskStage.TASK_ACCEPTED
        self.csv_path = options['csv_data_file']
        self.rivm_format = 'RIVM2016.V1'
        self._init_parser()
        # self.rivm_format = options['rivm_format']

        self.stdout.write('Starting to import: %s\n' % self.csv_path)
        f = None
        try:
            f = open(self.csv_path)
            self.csv_reader = csv.reader(f)

            self.stdout.write('Loaded csv file: %s\n' % self.csv_path)
            self.task_stage = TaskStage.TASK_CSV_LOADED

            row1 = next(self.csv_reader)
            row2 = next(self.csv_reader)
            self._pre_process(row1, row2)

            self._load_indicators(row1, row2)
            self.stdout.write('Loaded Indicators: new %s, existing %s \n'
                              % (self.csv_loader_stats['indicators_new'],
                                 self.csv_loader_stats['indicators_existing'])
                              )

            self.stdout.write('Starting to import Entries and Impact rows.\n')
            for entry_data_row in self.csv_reader:
                self._process_row(entry_data_row)
                self.processed_rows += 1
                if self.processed_rows % self.progress_update_interval == 0:
                    self.stdout.write('Processed %d rows.' % self.processed_rows)

            self.stdout.write('Imported Entries: new %s, existing %s \n'
                              % (self.csv_loader_stats['entries_new'],
                                 self.csv_loader_stats['entries_existing'])
                              )
            self.stdout.write('Imported Impact data: new %s, existing %s \n'
                              % (self.csv_loader_stats['impacts_new'],
                                 self.csv_loader_stats['impacts_existing'])
                              )

            self._post_process()
            self.stdout.write('Finished importing %s\n' % self.csv_path)

        except Exception as ex:
            # TODO: catch specific exceptions.
            self.stdout.write('Something went wrong: %s\n' % ex)
            raise CommandError('Something went wrong: %s' % ex)
        finally:
            if f:
                f.close()

    def _init_parser(self):
        """
        TODO: initialize parser objects and constants for the given format version
        :return:
        """
        self.geo_key_regex = csv_import_format[self.rivm_format]['geo_key_regex']
        return

    def _load_indicators(self, row1, row2):
        """
        Parse header lines for Indicators or any other metadata
        1. Save Indicators to database model, and
        2. Cache locally for processing entries, in-memory cache is
        :return:
        """
        # first row of the CSV file contains Indicator Headers
        indicator_header = row1
        # Second row of the CSV file contains Indicator units
        indicator_units = row2

        for csv_column_index, (ih, iu) in enumerate(zip(indicator_header, indicator_units)):
            if ih is None or iu is None:
                # TODO: record ignored column count in csv_loader_stats
                continue
            else:
                unit = iu.strip()
                fields = [f for f in
                          map(str.strip,
                              ih.split(self.INDICATOR_FIELD_SEPARATOR)
                              )
                          ]
                if len(fields) != self.INDICATOR_FIELD_COUNT:
                    # TODO: use regex + filter for format validation
                    # TODO: Log a warning for badly formatted column
                    # TODO: save ignored column count in csv_loader_stats
                    continue

            # TODO: map the field names with data model fields
            temp_indicator = {
                'method': fields[0],
                'category': fields[1],
                'indicator': fields[2],
                'unit': unit
            }
            indicator, created = Indicator.objects.get_or_create(**temp_indicator)
            self.indicator_cache[csv_column_index] = indicator
            if created:
                self.csv_loader_stats['indicators_new'] += 1
            else:
                self.csv_loader_stats['indicators_existing'] += 1

        return

    def _process_row(self, entry_data_row):
        """
        :param entry_data_row:
        :return:
        """
        ecoinvent_column_data = entry_data_row[1].strip()
        unit = entry_data_row[2].strip()
        quantity = float(entry_data_row[3].strip())
        fields = [f for f in
                  map(str.strip,
                      ecoinvent_column_data.split(self.ENTRY_FIELD_SEPARATOR)
                      )
                  ]
        geo = None
        if len(fields) != self.ENTRY_FIELD_COUNT:
            # TODO: log info/warning and return
            return

        try:
            geo_key = self.geo_key_regex.search(fields[1]).group(1)
            geo = Geography.objects.get(id=geo_key)
        except Exception as ex:
            # TODO: Catch specific exceptions:
            #  a) Can not extract geo_key from the column data
            #  b) Geography not found in db
            return

        # All of the fields, and geo key should non-null
        if not all([fields[0], fields[1], unit]):
            # TODO: log warning for badly formatted column_data
            self.stdout.write('WARNING: one of the required fields is None')
            return

        temp_entry = {
            'product_name': fields[0],
            'geography': geo,
            'unit': unit,
            'quantity': quantity
        }

        entry, created = Entry.objects.get_or_create(**temp_entry)
        if created:
            self.csv_loader_stats['entries_new'] += 1
        else:
            self.csv_loader_stats['entries_existing'] += 1

        # For each valid row entry, with a value corresponding to an Indicator Column:
        # create impact objects, indicators start at 6th column (#5)
        # or min(self.indicator_cache.keys())
        for column_idx, column_value in enumerate(entry_data_row):
            # ignore first 5 columns, and the empty column_values
            if column_idx < self.INDICATOR_COLUMN_START_INDEX or not column_value:
                continue
            coefficient = float(column_value)
            indicator = self.indicator_cache.get(column_idx, None)
            if not indicator or not coefficient:
                # Ignore no indicator, or 0 coefficient
                # TODO: log warning and continue
                continue
            temp_impact = {
                'entry': entry,
                'indicator': indicator,
                'coefficient': coefficient
            }
            impact, created = Impact.objects.get_or_create(**temp_impact)
            if created:
                self.csv_loader_stats['impacts_new'] += 1
            else:
                self.csv_loader_stats['impacts_existing'] += 1

        return

    def _pre_process(self, row1, row2):
        """
        Place holder for performing pre processing actions
        # TODO: this should perform format validation.
        E.g.
        1. Which format the CSV conforms to - RIVM2016.V1 or RIVM2016.V2 or RIVM2020.V1 ...
        2. Whether any pre-requisite seeds are loaded
        :return:
        """
        validated = self._validate_header_format() and self._ensure_seeds()
        return validated

    def _ensure_seeds(self):
        """
        TODO: Ensure the seeds required for this format are loaded
        :param format:
        :return: Boolean
        """
        return True

    def _validate_header_format(self):
        """
        TODO: Validate the header against the format version
        :return:
        """
        return True

    def _post_process(self):
        """
        TODO: Place holder for performing post processing actions
        E.g. any callbacks, email, slack reporting
        :return:
        """
        return True
