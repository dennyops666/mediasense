from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0006_alter_alertrule_is_active'),
    ]

    operations = [
        migrations.RenameField(
            model_name='alertrule',
            old_name='is_active',
            new_name='is_enabled',
        ),
    ] 