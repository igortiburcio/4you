from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('employees', '0004_backfill_birth_date_and_position'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='employee',
            name='position',
        ),
        migrations.RenameField(
            model_name='employee',
            old_name='position_ref',
            new_name='position',
        ),
        migrations.AlterField(
            model_name='employee',
            name='position',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='employees', to='employees.position'),
        ),
        migrations.AlterField(
            model_name='employee',
            name='birth_date',
            field=models.DateField(),
        ),
        migrations.RemoveField(
            model_name='employee',
            name='age',
        ),
    ]
