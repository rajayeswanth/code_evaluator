import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from evaluation.models import Rubric


class Command(BaseCommand):
    help = 'Load rubrics from rubrics.json file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='rubrics.json',
            help='Path to the rubrics JSON file'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing rubrics'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        force_update = options['force']
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'Rubrics file not found: {file_path}')
            )
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rubrics_data = json.load(f)
            
            created_count = 0
            updated_count = 0
            
            for filename, rubric_data in rubrics_data.items():
                # Check if rubric already exists
                existing_rubric = Rubric.objects.filter(filename=filename).first()
                
                if existing_rubric and not force_update:
                    self.stdout.write(
                        self.style.WARNING(f'Rubric {filename} already exists. Use --force to update.')
                    )
                    continue
                
                rubric_dict = {
                    'name': f'Rubric for {filename}',
                    'filename': filename,
                    'total_points': rubric_data['total_points'],
                    'criteria': rubric_data['criteria']
                }
                
                if existing_rubric and force_update:
                    # Update existing rubric
                    for key, value in rubric_dict.items():
                        setattr(existing_rubric, key, value)
                    existing_rubric.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated rubric: {filename}')
                    )
                else:
                    # Create new rubric
                    Rubric.objects.create(**rubric_dict)
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created rubric: {filename}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully processed {len(rubrics_data)} rubrics. '
                    f'Created: {created_count}, Updated: {updated_count}'
                )
            )
            
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'Invalid JSON in {file_path}: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading rubrics: {str(e)}')
            ) 